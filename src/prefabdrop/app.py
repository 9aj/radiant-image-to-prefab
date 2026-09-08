from .paths import APP_ROOT
from .paths import APP_ROOT
"""Local GUI and CLI. Images never leave this computer."""
import argparse
import json
from dataclasses import asdict
from pathlib import Path
from PIL import Image
from .core import Settings, build, map_text, preview


def export(image, settings, target):
    mask, boxes = build(image, settings)
    target = Path(target)
    target.write_text(map_text(boxes, settings.material), encoding='utf-8')
    return mask, boxes


def gui():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from PIL import ImageTk
    root = tk.Tk()
    root.title('Image â†’ Radiant | Brush prefab workshop')
    root.geometry('1160x780')
    root.minsize(920,620)
    root.configure(bg='#141b20')
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('TFrame',background='#141b20')
    style.configure('TLabel',background='#141b20',foreground='#dce4da',font=('Segoe UI',10))
    style.configure('TButton',padding=8,font=('Segoe UI',10))
    state = {'image':None,'path':None}
    header=ttk.Frame(root,padding=18); header.pack(fill='x')
    ttk.Label(header,text='IMAGE â†’ RADIANT',font=('Segoe UI',20,'bold')).pack(anchor='w')
    ttk.Label(header,text='Silhouette to editable CoD4 brushes â€¢ local processing â€¢ iwmap 4').pack(anchor='w')
    body=ttk.Frame(root,padding=(18,0)); body.pack(fill='both',expand=True)
    controls=ttk.Frame(body,width=240); controls.pack(side='left',fill='y',padx=(0,18))
    viewport=ttk.Frame(body); viewport.pack(side='left',fill='both',expand=True)
    display=tk.Label(viewport,bg='#141b20',text='Open an image or load the honeycomb example.',fg='#dce4da')
    display.pack(fill='both',expand=True)
    status=tk.StringVar(value='Ready. Black shapes on white work best; use Alpha for transparent PNGs.')
    ttk.Label(root,textvariable=status,padding=18,wraplength=1080).pack(fill='x')
    variables={}
    defaults=asdict(Settings())
    for key,label,choices in [
        ('mode','Solid pixels',('dark','light','alpha')),
        ('resolution','Longest edge (4â€“512 cells)',None),
        ('threshold','Threshold (0â€“255)',None),
        ('cell','Units per cell',None),
        ('depth','Extrusion depth (units)',None),
        ('orientation','Orientation',('floor','wall')),
        ('material','Material (placeholder)',None),
        ('max_brushes','Maximum brushes',None),
    ]:
        ttk.Label(controls,text=label).pack(anchor='w',pady=(8,2))
        var=tk.StringVar(value=str(defaults[key])); variables[key]=var
        widget=ttk.Combobox(controls,textvariable=var,values=choices,state='readonly') if choices else ttk.Entry(controls,textvariable=var)
        widget.pack(fill='x')
    def settings():
        values={k:v.get() for k,v in variables.items()}
        for k in ('resolution','threshold','max_brushes'): values[k]=int(values[k])
        for k in ('cell','depth'): values[k]=float(values[k])
        result=Settings(**values); result.validate(); return result
    def render():
        if state['image'] is None: raise ValueError('Open an image first.')
        s=settings(); mask,boxes=build(state['image'],s)
        picture=preview(mask,boxes,(max(540,display.winfo_width()),max(380,display.winfo_height())))
        state['photo']=ImageTk.PhotoImage(picture)
        display.configure(image=state['photo'],text='')
        width,height=len(mask[0])*s.cell,len(mask)*s.cell
        status.set(f'{state["path"].name} â€¢ {len(boxes):,} brushes â€¢ image plane {width:g} Ã— {height:g} units â€¢ depth {s.depth:g}. Preview uses current settings.')
        return s,mask,boxes
    def guarded(fn):
        def run():
            try: fn()
            except Exception as e:
                status.set('Action failed. Correct the settings and update the preview.')
                messagebox.showerror('Image â†’ Radiant',str(e))
        return run
    def load(path=None):
        path=path or filedialog.askopenfilename(filetypes=[('Images','*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff'),('All files','*.*')])
        if not path: return
        with Image.open(path) as im: image=im.copy()
        state.update(image=image,path=Path(path)); render()
    def save():
        s,mask,boxes=render()
        path=filedialog.asksaveasfilename(defaultextension='.map',initialfile=state['path'].stem+'_prefab.map',filetypes=[('CoD4 map prefab','*.map')])
        if path:
            Path(path).write_text(map_text(boxes,s.material),encoding='utf-8')
            status.set(f'Exported {len(boxes):,} brushes to {path}. Open in Radiant to check scale and geometry. Caulk must be replaced on visible faces.')
    ttk.Button(controls,text='Open imageâ€¦',command=guarded(load)).pack(fill='x',pady=(18,4))
    ttk.Button(controls,text='Load honeycomb example',command=guarded(lambda:load(APP_ROOT/'examples'/'honeycomb.png'))).pack(fill='x',pady=4)
    ttk.Button(controls,text='Update preview',command=guarded(render)).pack(fill='x',pady=4)
    ttk.Button(controls,text='Export .mapâ€¦',command=guarded(save)).pack(fill='x',pady=4)
    for v in variables.values():
        v.trace_add('write',lambda *_:status.set('Settings changed. Update preview or export to regenerate geometry.'))
    root.mainloop()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image',nargs='?')
    parser.add_argument('-o','--output',type=Path)
    parser.add_argument('--resolution',type=int,default=96)
    parser.add_argument('--threshold',type=int,default=128)
    parser.add_argument('--mode',choices=['dark','light','alpha'],default='dark')
    parser.add_argument('--cell',type=float,default=4)
    parser.add_argument('--depth',type=float,default=32)
    parser.add_argument('--orientation',choices=['floor','wall'],default='floor')
    parser.add_argument('--material',default='caulk')
    parser.add_argument('--max-brushes',type=int,default=4096)
    parser.add_argument('--preview',type=Path,help='Optional preview PNG output')
    args=parser.parse_args()
    if not args.image:
        gui(); return
    if not args.output: parser.error('--output is required with an image')
    try:
        s=Settings(**{k:getattr(args,k) for k in asdict(Settings())})
        with Image.open(args.image) as im: mask,boxes=export(im,s,args.output)
        if args.preview: preview(mask,boxes).save(args.preview)
        print(json.dumps({'output':str(args.output),'brushes':len(boxes),'faces':len(boxes)*6,'settings':asdict(s)},indent=2))
    except (ValueError,OSError) as e:
        parser.exit(1,f'Error: {e}\n')


if __name__=='__main__': main()
