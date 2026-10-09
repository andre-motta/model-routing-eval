from __future__ import annotations

import logging
import typing

from packaging.requirements import Requirement
from packaging.version import Version
from resolvelib.resolvers import ResolverException

from .. import context, resolver, sources, wheels
from ..requirements_file import RequirementType
from ._phase import Phase
from ._prepare_source import PrepareSource
from ._types import BootstrapPhase

if typing.TYPE_CHECKING:
    from ._bootstrapper import Bootstrapper

logger = logging.getLogger(__name__)


def _re_resolve_url(
    ctx: context.WorkContext,
    req: Requirement,
    req_type: RequirementType,
    resolved_version: Version,
    pre_built: bool,
    cache_wheel_server_url: str | None,
) -> str | None:
    """Resolve the download URL for *resolved_version* of the requested kind.

    Used when the version-specific ``pre_built`` setting differs from the
    variant default, so the URL from the RESOLVE phase is the wrong kind.
    Returns ``None`` if no matching distribution was found.
    """
    pinned = Requirement(f"{req.name}=={resolved_version}")
    if pre_built:
        wheel_server_urls = wheels.get_wheel_server_urls(
            ctx,
            pinned,
            cache_wheel_server_url=cache_wheel_server_url,
            version=resolved_version,
        )
        try:
            url, _ = wheels.resolve_prebuilt_wheel(
                ctx=ctx,
                req=pinned,
                wheel_server_urls=wheel_server_urls,
                req_type=req_type,
            )
        except ExceptionGroup:
            return None
        return str(url)

    pbi = ctx.package_build_info(req)
    provider = sources.get_source_provider(
        ctx=ctx,
        req=pinned,
        sdist_server_url=pbi.resolver_sdist_server_url(resolver.PYPI_SERVER_URL),
        req_type=req_type,
    )
    try:
        results = resolver.find_all_matching_from_provider(provider, pinned)
    except ResolverException:
        return None
    if not results:
        return None
    url, _ = results[0]
    return url


class Start(Phase):
    """Record a resolved requirement in the dependency graph and deduplicate.

    Re-resolves the download URL when the version's ``pre_built`` setting
    differs from the variant default.  Then adds the ``(parent → req)`` edge
    to the dependency graph, and checks whether this ``(req, version)`` pair
    has already been processed.  Duplicate requirements are silently dropped;
    new ones proceed to source preparation.
    ``tracks_why`` is ``False`` so graph additions happen before the why-stack
    is updated.

    Next phase: ``PrepareSource`` (new requirement) or ``[]`` (already seen).
    """

    phase: typing.ClassVar[BootstrapPhase] = BootstrapPhase.START
    tracks_why: typing.ClassVar[bool] = False

    def run(self, bt: Bootstrapper) -> list[Phase]:
        """START phase: add to graph, check if already seen.

        _track_why is a no-op for this phase (tracks_why is False),
        matching the original behavior where graph addition and
        seen-check happen before pushing onto the why stack.

        Returns:
            Empty list if already seen (nothing to do).
            [PrepareSource] if this is new work.
        """
        wi = self.work_item
        assert wi.resolved_version is not None
        assert wi.source_url is not None

        # Must run before the graph update and seen-check so the graph stores
        # the final URL and every parent edge is recorded.
        pbi = bt.ctx.package_build_info(wi.req)
        wi.pbi_pre_built = pbi.is_pre_built(wi.resolved_version)
        if wi.pbi_pre_built != pbi.pre_built or (
            wi.pbi_pre_built
            and pbi.get_wheel_server_url(wi.resolved_version) != pbi.wheel_server_url
        ):
            logger.info(
                f"{wi.req} {wi.resolved_version}: re-resolving download URL "
                f"(pre_built={wi.pbi_pre_built})"
            )
            new_url = _re_resolve_url(
                bt.ctx,
                wi.req,
                wi.req_type,
                wi.resolved_version,
                wi.pbi_pre_built,
                bt.cache_wheel_server_url,
            )
            if new_url is None:
                logger.warning(
                    f"{wi.req} {wi.resolved_version}: no download URL found "
                    f"for pre_built={wi.pbi_pre_built}, keeping {wi.source_url}"
                )
            else:
                wi.source_url = new_url

        # Add to graph (skip TOP_LEVEL, already added in _resolve_and_add_top_level)
        if wi.req_type != RequirementType.TOP_LEVEL:
            bt.add_to_graph(
                wi.req,
                wi.req_type,
                wi.resolved_version,
                wi.source_url,
                wi.parent,
            )

        wi.build_sdist_only = bt.sdist_only and not wi.is_build_requirement_context()

        if bt.has_been_seen(wi.req, wi.resolved_version, wi.build_sdist_only):
            logger.debug(
                f"redundant {wi.req_type} dependency {wi.req} "
                f"({wi.resolved_version}, sdist_only={wi.build_sdist_only}) "
                f"for {bt.explain}"
            )
            return []
        bt.mark_as_seen(wi.req, wi.resolved_version, wi.build_sdist_only)

        logger.info(
            f"new {wi.req_type} dependency {wi.req} resolves to {wi.resolved_version}"
        )

        wi.exclusive_build = pbi.exclusive_build
        return [PrepareSource(wi)]
