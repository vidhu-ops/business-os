"""IIDATECH domain classification and routing."""
from iidatech.routing.domain_router import classify_domain_with_trace, get_last_routing_trace, route_domain, should_block_domain
__all__ = ["classify_domain_with_trace", "get_last_routing_trace", "route_domain", "should_block_domain"]