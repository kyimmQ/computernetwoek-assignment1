import tkinter as tk

class ConsoleText(tk.Text):

    def __init__(self, master=None, **kw):
        tk.Text.__init__(self, master, **kw)
        
        self.insert('1.0', '''Server terminal for file tranfering application
help - Print all commands and usage
list - List all client with files
ping client_addr - Live check client at client_addr
discover client_addr - Discover files in local repository of client at client_addr
quit - Shut down server socket. Use
>>> ''') # first prompt
        # create input mark
        self.tag_configure("sel", background="blue")
        self.mark_set('input', 'insert')
        self.mark_gravity('input', 'left')
        # create proxy
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)
        self.bind("<Control-c>", self.copy)  # Bind Ctrl+C to copy
        self.bind("<Control-v>", self.paste)  # Bind Ctrl+V to paste

    def _proxy(self, *args):
        largs = list(args)
        if args[0] == 'insert':
            if self.compare('insert', '<', 'input'):
                # move insertion cursor to the editable part
                self.mark_set('insert', 'end')  # you can change 'end' with 'input'
        elif args[0] == "delete":
            if self.compare(largs[1], '<', 'input'):
                if len(largs) == 2:
                    return # don't delete anything
                largs[1] = 'input'  # move deletion start at 'input'
        result = self.tk.call((self._orig,) + tuple(largs))
        return result

    def copy(self, event):
        # Handle Ctrl+C
        text = self.get("sel.first", "sel.last")
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
        return 'break' # prevent default behavior like going to proxy function

    def paste(self, event):
        # Handle Ctrl+V
        text = self.clipboard_get()
        self.insert("input", text)
        return 'break' # prevent default behavior like going to proxy function
        
    