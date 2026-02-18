"""
Adapter for BezierSegmentManager

Simple pass-through adapter that exposes BezierSegmentManager directly.
The BezierSegmentManager already implements everything the ContourEditor needs.
"""


class BezierSegmentManagerAdapter:
    """
    Simplified adapter that just exposes BezierSegmentManager directly.

    The BezierSegmentManager already has all the methods and attributes
    that ContourEditor needs, so we don't need to wrap anything.
    """

    def __init__(self):
        """Initialize with lazy import of concrete BezierSegmentManager"""
        # Lazy import to avoid circular dependencies
        from contour_editor import BezierSegmentManager
        self._manager = BezierSegmentManager()

    def __getattr__(self, name):
        """
        Forward all attribute/method access directly to the wrapped manager.

        This makes the adapter completely transparent - it just passes through
        to the real BezierSegmentManager.
        """
        return getattr(self._manager, name)

