from __future__ import annotations

import logging
import typing

from packaging.requirements import Requirement
from packaging.version import Version
from resolvelib.resolvers import ResolverException

from .. import resolver, sources, wheels
from ..requirements_file import RequirementType
from ._phase import Phase
from ._prepare_source import PrepareSource
from ._types import BootstrapPhase

if typing.TYPE_CHECKING:
    from .. import context
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
    """Find the download URL of *resolved_version* as a pre-built wheel or sdist.

    Used when the version-specific ``pre_built`` setting differs from the one
    the URL was resolved with. Returns ``None`` if no matching file is found.
    """
    pinned = Requirement(f"{req.name}=={Version(resolved_version.public)}")
    if pre_built:
        wheel_server_urls = wheels.get_wheel_server_urls(
            ctx,
            req,
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
        return url

    provider = sources.get_source_provider(
        ctx=ctx,
        req=pinned,
        sdist_server_url=resolver.PYPI_SERVER_URL,
        req_type=req_type,
    )
    try:
        results = resolver.find_all_matching_from_provider(provider, pinned)
    except ResolverException:
        return None
    url, _ = results[0]
    return url


class Start(Phase):
    """Record a resolved requirement in the dependency graph and deduplicate.

    Sets the version-specific ``pre_built`` state and, if it differs from the
    state used to resolve the download URL, re-resolves the URL. Then adds the
    ``(parent → req)`` edge to the dependency graph and checks whether this
    ``(req, version)`` pair has already been processed.  Duplicate requirements
    are silently dropped; new ones proceed to source preparation.
    ``tracks_why`` is ``False`` so graph additions happen before the why-stack
    is updated.

    Next phase: ``PrepareSource`` (new requirement) or ``[]`` (already seen).
    """

    phase: typing.ClassVar[BootstrapPhase] = BootstrapPhase.START
    tracks_why: typing.ClassVar[bool] = False

    def run(self, bt: Bootstrapper) -> list[Phase]:
        """START phase: fix the download URL, add to graph, check if already seen.

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

        # Must set pbi_pre_built before constructing PrepareSource so that
        # PrepareSource.background_work() immediately sees the correct value.
        pbi = bt.ctx.package_build_info(wi.req)
        wi.pbi_pre_built = pbi.is_pre_built(wi.resolved_version)

        # The URL was resolved with the pre_built setting in effect before the
        # version was known. Re-resolve it if the version needs another kind of
        # download. Must run before the graph add so the graph stores the URL.
        if wi.pbi_pre_built != pbi.pre_built or (
            wi.pbi_pre_built
            and pbi.get_wheel_server_url(wi.resolved_version) != pbi.wheel_server_url
        ):
            logger.info(
                f"re-resolving download url for {wi.req} {wi.resolved_version} "
                f"with pre_built={wi.pbi_pre_built}"
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
                    f"no pre_built={wi.pbi_pre_built} download found for {wi.req} "
                    f"{wi.resolved_version}, keeping {wi.source_url}"
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
