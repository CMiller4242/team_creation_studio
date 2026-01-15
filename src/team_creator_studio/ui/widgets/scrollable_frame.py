"""
Scrollable frame widget.

Provides a frame with automatic scrollbars that works reliably on all platforms.
"""

import tkinter as tk
from tkinter import ttk


class ScrollableFrame(ttk.Frame):
    """
    A frame that can be scrolled with automatic scrollbars.

    Usage:
        scrollable = ScrollableFrame(parent)
        scrollable.pack(fill="both", expand=True)

        # Add widgets to scrollable.scrollable_frame instead of scrollable
        label = ttk.Label(scrollable.scrollable_frame, text="Content")
        label.pack()
    """

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Create canvas
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)

        # Create scrollbars
        self.v_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)

        # Create the scrollable frame
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Configure canvas scrolling
        self.canvas.configure(
            yscrollcommand=self.v_scrollbar.set,
            xscrollcommand=self.h_scrollbar.set
        )

        # Create window in canvas for the frame
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw"
        )

        # Bind configuration events
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Bind mouse wheel events
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

        # Layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Configure grid weights
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def _on_frame_configure(self, event=None):
        """Update scroll region when frame size changes."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """Update frame width when canvas size changes."""
        # Make the scrollable frame fill the canvas width
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        # Get widget under mouse
        widget = self.winfo_containing(event.x_root, event.y_root)

        # Only scroll if mouse is over this canvas or its children
        if widget and (widget == self.canvas or self._is_child_of(widget, self.canvas)):
            if event.num == 5 or event.delta < 0:
                # Scroll down
                self.canvas.yview_scroll(1, "units")
            elif event.num == 4 or event.delta > 0:
                # Scroll up
                self.canvas.yview_scroll(-1, "units")

    def _is_child_of(self, widget, parent):
        """Check if widget is a child of parent."""
        current = widget
        while current:
            if current == parent:
                return True
            current = current.master
        return False

    def scroll_to_top(self):
        """Scroll to the top of the frame."""
        self.canvas.yview_moveto(0)

    def scroll_to_bottom(self):
        """Scroll to the bottom of the frame."""
        self.canvas.yview_moveto(1)
