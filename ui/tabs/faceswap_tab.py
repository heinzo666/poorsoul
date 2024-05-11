import os
import shutil
import pathlib
import gradio as gr
import roop.utilities as util
import roop.globals
import ui.globals
from roop.face_util import extract_face_images, create_blank_image
from roop.capturer import get_video_frame, get_video_frame_total, get_image_frame
from roop.ProcessEntry import ProcessEntry
from roop.FaceSet import FaceSet

last_image = None


IS_INPUT = True
SELECTED_FACE_INDEX = 0

SELECTED_INPUT_FACE_INDEX = 0
SELECTED_TARGET_FACE_INDEX = 0

input_faces = None
target_faces = None
face_selection = None
previewimage = None

selected_preview_index = 0

is_processing = False            

list_files_process : list[ProcessEntry] = []
no_face_choices = ["Use untouched original frame","Retry rotated", "Skip Frame"]

current_video_fps = 50

manual_masking = False


def faceswap_tab():
    global no_face_choices, previewimage

    with gr.Tab("🎭 Face Swap"):
        with gr.Row(variant='panel'):
            with gr.Column(scale=2):
                with gr.Row():
                    with gr.Column(min_width=160):
                        input_faces = gr.Gallery(label="Input faces", allow_preview=False, preview=False, height=128, object_fit="scale-down", columns=8)
                        with gr.Accordion(label="Advanced Masking", open=False):
                            chk_showmaskoffsets = gr.Checkbox(label="Show mask overlay in preview", value=False, interactive=True)
                            mask_top = gr.Slider(0, 1.0, value=0, label="Offset Face Top", step=0.01, interactive=True)
                            mask_bottom = gr.Slider(0, 1.0, value=0, label="Offset Face Bottom", step=0.01, interactive=True)
                            mask_left = gr.Slider(0, 1.0, value=0, label="Offset Face Left", step=0.01, interactive=True)
                            mask_right = gr.Slider(0, 1.0, value=0, label="Offset Face Right", step=0.01, interactive=True)
                            mask_erosion = gr.Slider(1.0, 3.0, value=1.0, label="Erosion Iterations", step=1.00, interactive=True)
                            mask_blur = gr.Slider(10.0, 50.0, value=20.0, label="Blur size", step=1.00, interactive=True)
                            bt_toggle_masking = gr.Button("Toggle manual masking", variant='secondary', size='sm')
                            chk_useclip = gr.Checkbox(label="Use Text Masking", value=False)
                            clip_text = gr.Textbox(label="List of objects to mask and restore back on fake image", value="cup,hands,hair,banana" ,elem_id='tooltip')
                            gr.Dropdown(["Clip2Seg"], value="Clip2Seg", label="Engine")
                            bt_preview_mask = gr.Button("👥 Show Mask Preview", variant='secondary')
                        bt_remove_selected_input_face = gr.Button("❌ Remove selected", size='sm')
                        bt_clear_input_faces = gr.Button("💥 Clear all", variant='stop', size='sm')
                    with gr.Column(min_width=160):
                        target_faces = gr.Gallery(label="Target faces", allow_preview=False, preview=False, height=128, object_fit="scale-down", columns=8)
                        bt_remove_selected_target_face = gr.Button("❌ Remove selected", size='sm')
                        bt_add_local = gr.Button('Add local files from', size='sm')
                        local_folder = gr.Textbox(show_label=False, placeholder="/content/", interactive=True)
                with gr.Row(variant='panel'):
                    bt_srcfiles = gr.Files(label='Source File(s)', file_count="multiple", file_types=["image", ".fsz"], elem_id='filelist', height=233)
                    bt_destfiles = gr.Files(label='Target File(s)', file_count="multiple", file_types=["image", "video"], elem_id='filelist', height=233)
                with gr.Row(variant='panel'):
                    gr.Markdown('')
                    forced_fps = gr.Slider(minimum=0, maximum=120, value=0, label="Video FPS", info='Overrides detected fps if not 0', step=1.0, interactive=True, container=True)

            with gr.Column(scale=2):
                previewimage = gr.Image(label="Preview Image", height=576, interactive=False, visible=True)
                maskimage = gr.ImageEditor(label="Manual mask Image", sources=["clipboard"], transforms="", type="numpy",
                                             brush=gr.Brush(color_mode="fixed", colors=["rgba(255, 255, 255, 1"]), interactive=True, visible=False)
                with gr.Row(variant='panel'):
                        fake_preview = gr.Checkbox(label="Face swap frames", value=False)
                        bt_refresh_preview = gr.Button("🔄 Refresh", variant='secondary', size='sm')
                        bt_use_face_from_preview = gr.Button("Use Face from this Frame", variant='primary', size='sm')
                with gr.Row():
                    preview_frame_num = gr.Slider(1, 1, value=1, label="Frame Number", info='0:00:00', step=1.0, interactive=True)
                with gr.Row():
                    text_frame_clip = gr.Markdown('Processing frame range [0 - 0]')
                    set_frame_start = gr.Button("⬅ Set as Start", size='sm')
                    set_frame_end = gr.Button("➡ Set as End", size='sm')
        with gr.Row(visible=False) as dynamic_face_selection:
            with gr.Column(scale=2):
                face_selection = gr.Gallery(label="Detected faces", allow_preview=False, preview=False, height=256, object_fit="cover", columns=8)
            with gr.Column():
                bt_faceselect = gr.Button("☑ Use selected face", size='sm')
                bt_cancelfaceselect = gr.Button("Done", size='sm')
            with gr.Column():
                gr.Markdown(' ') 
    
        with gr.Row(variant='panel'):
            with gr.Column(scale=1):
                selected_face_detection = gr.Dropdown(["First found", "All female", "All male", "All faces", "Selected face"], value="First found", label="Specify face selection for swapping")
                max_face_distance = gr.Slider(0.01, 1.0, value=0.65, label="Max Face Similarity Threshold")
                video_swapping_method = gr.Dropdown(["Extract Frames to media","In-Memory processing"], value="In-Memory processing", label="Select video processing method", interactive=True)
                no_face_action = gr.Dropdown(choices=no_face_choices, value=no_face_choices[0], label="Action on no face detected", interactive=True)
                vr_mode = gr.Checkbox(label="VR Mode", value=False)
            with gr.Column(scale=1):
                ui.globals.ui_selected_enhancer = gr.Dropdown(["None", "Codeformer", "DMDNet", "GFPGAN", "GPEN", "Restoreformer++"], value="None", label="Select post-processing")
                ui.globals.ui_blend_ratio = gr.Slider(0.0, 1.0, value=0.65, label="Original/Enhanced image blend ratio")
                with gr.Group():
                    autorotate = gr.Checkbox(label="Auto rotate horizontal Faces", value=True)
                    roop.globals.skip_audio = gr.Checkbox(label="Skip audio", value=False)
                    roop.globals.keep_frames = gr.Checkbox(label="Keep Frames (relevant only when extracting frames)", value=False)
                    roop.globals.wait_after_extraction = gr.Checkbox(label="Wait for user key press before creating video ", value=False)
        with gr.Row(variant='panel'):
            with gr.Column():
                bt_start = gr.Button("▶ Start", variant='primary')
                gr.Button("👀 Open Output Folder", size='sm').click(fn=lambda: util.open_folder(roop.globals.output_path))
            with gr.Column():
                bt_stop = gr.Button("⏹ Stop", variant='secondary', interactive=False)
            with gr.Column(scale=2):
                gr.Markdown(' ') 
        with gr.Row(variant='panel'):
            with gr.Column():
                resultfiles = gr.Files(label='Processed File(s)', interactive=False)
            with gr.Column():
                resultimage = gr.Image(type='filepath', label='Final Image', interactive=False )
                resultvideo = gr.Video(label='Final Video', interactive=False, visible=False)

    previewinputs = [preview_frame_num, bt_destfiles, fake_preview, ui.globals.ui_selected_enhancer, selected_face_detection,
                        max_face_distance, ui.globals.ui_blend_ratio, chk_useclip, clip_text, no_face_action, vr_mode, autorotate, maskimage, chk_showmaskoffsets]
    previewoutputs = [previewimage, maskimage, preview_frame_num] 
    input_faces.select(on_select_input_face, None, None).then(fn=on_preview_frame_changed, inputs=previewinputs, outputs=previewoutputs)
    bt_remove_selected_input_face.click(fn=remove_selected_input_face, outputs=[input_faces])
    bt_srcfiles.change(fn=on_srcfile_changed, show_progress='full', inputs=bt_srcfiles, outputs=[dynamic_face_selection, face_selection, input_faces])

    mask_top.release(fn=on_mask_top_changed, inputs=[mask_top], show_progress='hidden')
    mask_bottom.release(fn=on_mask_bottom_changed, inputs=[mask_bottom], show_progress='hidden')
    mask_left.release(fn=on_mask_left_changed, inputs=[mask_left], show_progress='hidden')
    mask_right.release(fn=on_mask_right_changed, inputs=[mask_right], show_progress='hidden')
    mask_erosion.release(fn=on_mask_erosion_changed, inputs=[mask_erosion], show_progress='hidden')
    mask_blur.release(fn=on_mask_blur_changed, inputs=[mask_blur], show_progress='hidden')


    target_faces.select(on_select_target_face, None, None)
    bt_remove_selected_target_face.click(fn=remove_selected_target_face, outputs=[target_faces])

    forced_fps.change(fn=on_fps_changed, inputs=[forced_fps], show_progress='hidden')
    bt_destfiles.change(fn=on_destfiles_changed, inputs=[bt_destfiles], outputs=[preview_frame_num, text_frame_clip], show_progress='hidden').then(fn=on_preview_frame_changed, inputs=previewinputs, outputs=previewoutputs, show_progress='hidden')
    bt_destfiles.select(fn=on_destfiles_selected, outputs=[preview_frame_num, text_frame_clip, forced_fps], show_progress='hidden').then(fn=on_preview_frame_changed, inputs=previewinputs, outputs=previewoutputs, show_progress='hidden')
    bt_destfiles.clear(fn=on_clear_destfiles, outputs=[target_faces])
    resultfiles.select(fn=on_resultfiles_selected, inputs=[resultfiles], outputs=[resultimage, resultvideo])

    face_selection.select(on_select_face, None, None)
    bt_faceselect.click(fn=on_selected_face, outputs=[input_faces, target_faces, selected_face_detection])
    bt_cancelfaceselect.click(fn=on_end_face_selection, outputs=[dynamic_face_selection, face_selection])
    
    bt_clear_input_faces.click(fn=on_clear_input_faces, outputs=[input_faces])


    bt_add_local.click(fn=on_add_local_folder, inputs=[local_folder], outputs=[bt_destfiles])
    bt_preview_mask.click(fn=on_preview_mask, inputs=[preview_frame_num, bt_destfiles, clip_text], outputs=[previewimage]) 

    start_event = bt_start.click(fn=start_swap, 
        inputs=[ui.globals.ui_selected_enhancer, selected_face_detection, roop.globals.keep_frames, roop.globals.wait_after_extraction,
                    roop.globals.skip_audio, max_face_distance, ui.globals.ui_blend_ratio, chk_useclip, clip_text,video_swapping_method, no_face_action, vr_mode, autorotate, maskimage],
        outputs=[bt_start, bt_stop, resultfiles], show_progress='full')
    after_swap_event = start_event.then(fn=on_resultfiles_finished, inputs=[resultfiles], outputs=[resultimage, resultvideo])
    
    bt_stop.click(fn=stop_swap, cancels=[start_event, after_swap_event], outputs=[bt_start, bt_stop], queue=False)
    
    bt_refresh_preview.click(fn=on_preview_frame_changed, inputs=previewinputs, outputs=previewoutputs)            
    bt_toggle_masking.click(fn=on_toggle_masking, inputs=[previewimage, maskimage], outputs=[previewimage, maskimage])            
    fake_preview.change(fn=on_preview_frame_changed, inputs=previewinputs, outputs=previewoutputs)
    preview_frame_num.release(fn=on_preview_frame_changed, inputs=previewinputs, outputs=previewoutputs, show_progress='hidden', )
    bt_use_face_from_preview.click(fn=on_use_face_from_selected, show_progress='full', inputs=[bt_destfiles, preview_frame_num], outputs=[dynamic_face_selection, face_selection, target_faces, selected_face_detection])
    set_frame_start.click(fn=on_set_frame, inputs=[set_frame_start, preview_frame_num], outputs=[text_frame_clip])
    set_frame_end.click(fn=on_set_frame, inputs=[set_frame_end, preview_frame_num], outputs=[text_frame_clip])

                     
            
def on_mask_top_changed(mask_offset):
    set_mask_offset(0, mask_offset)

def on_mask_bottom_changed(mask_offset):
    set_mask_offset(1, mask_offset)

def on_mask_left_changed(mask_offset):
    set_mask_offset(2, mask_offset)

def on_mask_right_changed(mask_offset):
    set_mask_offset(3, mask_offset)

def on_mask_erosion_changed(mask_offset):
    set_mask_offset(4, mask_offset)
def on_mask_blur_changed(mask_offset):
    set_mask_offset(5, mask_offset)


def set_mask_offset(index, mask_offset):
    global SELECTED_INPUT_FACE_INDEX

    if len(roop.globals.INPUT_FACESETS) > SELECTED_INPUT_FACE_INDEX:
        offs = roop.globals.INPUT_FACESETS[SELECTED_INPUT_FACE_INDEX].faces[0].mask_offsets
        offs[index] = mask_offset
        if offs[0] + offs[1] > 0.99:
            offs[0] = 0.99
            offs[1] = 0.0
        if offs[2] + offs[3] > 0.99:
            offs[2] = 0.99
            offs[3] = 0.0
        roop.globals.INPUT_FACESETS[SELECTED_INPUT_FACE_INDEX].faces[0].mask_offsets = offs



def on_add_local_folder(folder):
    files = util.get_local_files_from_folder(folder)
    if files is None:
        gr.Warning("Empty folder or folder not found!")
    return files


def on_srcfile_changed(srcfiles, progress=gr.Progress()):
    from roop.face_util import norm_crop2
    global SELECTION_FACES_DATA, IS_INPUT, input_faces, face_selection, last_image
    
    IS_INPUT = True

    if srcfiles is None or len(srcfiles) < 1:
        return gr.Column(visible=False), None, ui.globals.ui_input_thumbs

    thumbs = []
    for f in srcfiles:    
        source_path = f.name
        if source_path.lower().endswith('fsz'):
            progress(0, desc="Retrieving faces from Faceset File")      
            unzipfolder = os.path.join(os.environ["TEMP"], 'faceset')
            if os.path.isdir(unzipfolder):
                files = os.listdir(unzipfolder)
                for file in files:
                    os.remove(os.path.join(unzipfolder, file))
            else:
                os.makedirs(unzipfolder)
            util.mkdir_with_umask(unzipfolder)
            util.unzip(source_path, unzipfolder)
            is_first = True
            face_set = FaceSet()
            for file in os.listdir(unzipfolder):
                if file.endswith(".png"):
                    filename = os.path.join(unzipfolder,file)
                    progress(0, desc="Extracting faceset")      
                    SELECTION_FACES_DATA = extract_face_images(filename,  (False, 0))
                    for f in SELECTION_FACES_DATA:
                        face = f[0]
                        face.mask_offsets = (0,0,0,0,1,20)
                        face_set.faces.append(face)
                        if is_first: 
                            image = util.convert_to_gradio(f[1])
                            ui.globals.ui_input_thumbs.append(image)
                            is_first = False
                        face_set.ref_images.append(get_image_frame(filename))
            if len(face_set.faces) > 0:
                if len(face_set.faces) > 1:
                    face_set.AverageEmbeddings()
                roop.globals.INPUT_FACESETS.append(face_set)
                                        
        elif util.has_image_extension(source_path):
            progress(0, desc="Retrieving faces from image")      
            roop.globals.source_path = source_path
            SELECTION_FACES_DATA = extract_face_images(roop.globals.source_path,  (False, 0))
            progress(0.5, desc="Retrieving faces from image")
            for f in SELECTION_FACES_DATA:
                face_set = FaceSet()
                face = f[0]
                face.mask_offsets = (0,0,0,0,1,20)
                face_set.faces.append(face)
                image = util.convert_to_gradio(f[1])
                ui.globals.ui_input_thumbs.append(image)
                roop.globals.INPUT_FACESETS.append(face_set)
                
    progress(1.0)

    # old style with selecting input faces commented out
    # if len(thumbs) < 1:     
    #     return gr.Column(visible=False), None, ui.globals.ui_input_thumbs
    # return gr.Column(visible=True), thumbs, gr.Gallery(visible=True)

    return gr.Column(visible=False), None, ui.globals.ui_input_thumbs


def on_select_input_face(evt: gr.SelectData):
    global SELECTED_INPUT_FACE_INDEX

    SELECTED_INPUT_FACE_INDEX = evt.index


def remove_selected_input_face():
    global SELECTED_INPUT_FACE_INDEX

    if len(roop.globals.INPUT_FACESETS) > SELECTED_INPUT_FACE_INDEX:
        f = roop.globals.INPUT_FACESETS.pop(SELECTED_INPUT_FACE_INDEX)
        del f
    if len(ui.globals.ui_input_thumbs) > SELECTED_INPUT_FACE_INDEX:
        f = ui.globals.ui_input_thumbs.pop(SELECTED_INPUT_FACE_INDEX)
        del f

    return ui.globals.ui_input_thumbs

def on_select_target_face(evt: gr.SelectData):
    global SELECTED_TARGET_FACE_INDEX

    SELECTED_TARGET_FACE_INDEX = evt.index

def remove_selected_target_face():
    if len(roop.globals.TARGET_FACES) > SELECTED_TARGET_FACE_INDEX:
        f = roop.globals.TARGET_FACES.pop(SELECTED_TARGET_FACE_INDEX)
        del f
    if len(ui.globals.ui_target_thumbs) > SELECTED_TARGET_FACE_INDEX:
        f = ui.globals.ui_target_thumbs.pop(SELECTED_TARGET_FACE_INDEX)
        del f
    return ui.globals.ui_target_thumbs





def on_use_face_from_selected(files, frame_num):
    global IS_INPUT, SELECTION_FACES_DATA

    IS_INPUT = False
    thumbs = []
    
    roop.globals.target_path = files[selected_preview_index].name
    if util.is_image(roop.globals.target_path) and not roop.globals.target_path.lower().endswith(('gif')):
        SELECTION_FACES_DATA = extract_face_images(roop.globals.target_path,  (False, 0))
        if len(SELECTION_FACES_DATA) > 0:
            for f in SELECTION_FACES_DATA:
                image = util.convert_to_gradio(f[1])
                thumbs.append(image)
        else:
            gr.Info('No faces detected!')
            roop.globals.target_path = None
                
    elif util.is_video(roop.globals.target_path) or roop.globals.target_path.lower().endswith(('gif')):
        selected_frame = frame_num
        SELECTION_FACES_DATA = extract_face_images(roop.globals.target_path, (True, selected_frame))
        if len(SELECTION_FACES_DATA) > 0:
            for f in SELECTION_FACES_DATA:
                image = util.convert_to_gradio(f[1])
                thumbs.append(image)
        else:
            gr.Info('No faces detected!')
            roop.globals.target_path = None

    if len(thumbs) == 1:
        roop.globals.TARGET_FACES.append(SELECTION_FACES_DATA[0][0])
        ui.globals.ui_target_thumbs.append(thumbs[0])
        return gr.Row(visible=False), None, ui.globals.ui_target_thumbs, gr.Dropdown(value='Selected face')

    return gr.Row(visible=True), thumbs, gr.Gallery(visible=True), gr.Dropdown(visible=True)



def on_select_face(evt: gr.SelectData):  # SelectData is a subclass of EventData
    global SELECTED_FACE_INDEX
    SELECTED_FACE_INDEX = evt.index
    

def on_selected_face():
    global IS_INPUT, SELECTED_FACE_INDEX, SELECTION_FACES_DATA
    
    fd = SELECTION_FACES_DATA[SELECTED_FACE_INDEX]
    image = util.convert_to_gradio(fd[1])
    if IS_INPUT:
        face_set = FaceSet()
        fd[0].mask_offsets = (0,0,0,0,1,20)
        face_set.faces.append(fd[0])
        roop.globals.INPUT_FACESETS.append(face_set)
        ui.
