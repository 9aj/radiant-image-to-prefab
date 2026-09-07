"""Standard-library GUI; conversion runs in the Pillow-enabled interpreter."""
import json
import base64
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

BASE=Path(__file__).resolve().parent


def main():
    worker=os.environ.get('RADIANT_WORKER_PYTHON',sys.executable)
    root=tk.Tk(); root.title('Image → Radiant | Prefab workshop'); root.geometry('1200x780')
    root.configure(bg='#141b20')
    style=ttk.Style(); style.theme_use('clam')
    style.configure('TFrame',background='#141b20')
    style.configure('TLabel',background='#141b20',foreground='#dce4da')
    style.configure('TButton',padding=8)
    ttk.Label(root,text='IMAGE → RADIANT',font=('Segoe UI',22,'bold'),padding=18).pack(anchor='w')
    body=ttk.Frame(root,padding=18); body.pack(fill='both',expand=True)
    controls=ttk.Frame(body); controls.pack(side='left',fill='y',padx=(0,18))
    display=tk.Label(body,bg='#141b20',fg='#dce4da',text='Open an image or load the honeycomb example.')
    display.pack(side='left',fill='both',expand=True)
    values={}; state={'source':None}; temp=tempfile.TemporaryDirectory(prefix='radiant-preview-')
    status=tk.StringVar(value='Local image processing • editable solid brushes • CoD4 iwmap 4')
    ttk.Label(root,textvariable=status,padding=18,wraplength=1120).pack(fill='x')
    for key,label,value,choices in [
        ('mode','Solid pixels','dark',['dark','light','alpha']),
        ('resolution','Longest edge (cells)','96',None),
        ('threshold','Threshold (0–255)','128',None),
        ('cell','Units per cell','4',None),
        ('depth','Extrusion depth','32',None),
        ('orientation','Orientation','floor',['floor','wall']),
        ('material','Placeholder material','caulk',None),
        ('max-brushes','Brush limit','4096',None),
    ]:
        ttk.Label(controls,text=label).pack(anchor='w',pady=(8,2))
        var=tk.StringVar(value=value); values[key]=var
        widget=ttk.Combobox(controls,textvariable=var,values=choices,state='readonly') if choices else ttk.Entry(controls,textvariable=var)
        widget.pack(fill='x')
        var.trace_add('write',lambda *_:status.set('Settings changed. Update preview to regenerate.'))
    def convert():
        if not state['source']: raise ValueError('Open an image first.')
        target=Path(temp.name)/'preview.map'; picture=Path(temp.name)/'preview.png'
        command=[worker,str(BASE/'app.py'),str(state['source']),'-o',str(target),'--preview',str(picture)]
        for key,var in values.items(): command.extend(['--'+key,var.get()])
        result=subprocess.run(command,capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        if result.returncode: raise ValueError(result.stderr.strip() or 'Conversion failed.')
        report=json.loads(result.stdout)
        photo=tk.PhotoImage(data=base64.b64encode(picture.read_bytes()).decode('ascii'))
        if display.winfo_width()<900: photo=photo.subsample(2)
        state['photo']=photo; display.configure(image=photo,text='')
        status.set(f'{Path(state["source"]).name} • {report["brushes"]:,} brushes • depth {report["settings"]["depth"]:g} units • preview current')
        return target
    def guard(fn):
        def wrapped():
            try: fn()
            except Exception as e: messagebox.showerror('Image → Radiant',str(e))
        return wrapped
    def load(path=None):
        path=path or filedialog.askopenfilename(filetypes=[('Images','*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff')])
        if path: state['source']=path; convert()
    def save():
        generated=convert()
        destination=filedialog.asksaveasfilename(defaultextension='.map',initialfile=Path(state['source']).stem+'_prefab.map',filetypes=[('CoD4 prefab','*.map')])
        if destination:
            Path(destination).write_bytes(generated.read_bytes())
            status.set(f'Exported {destination}. Check in Radiant and replace caulk on visible faces.')
    for label,action in [('Open image…',load),('Load honeycomb example',lambda:load(BASE/'examples'/'honeycomb.png')),('Update preview',convert),('Export .map…',save)]:
        ttk.Button(controls,text=label,command=guard(action)).pack(fill='x',pady=(8,0))
    try: root.mainloop()
    finally: temp.cleanup()


if __name__=='__main__': main()
