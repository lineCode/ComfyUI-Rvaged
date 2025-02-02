# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to
# deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import warnings
warnings.filterwarnings('ignore', module="torchvision")

from PIL import Image
import os
from datetime import datetime
import folder_paths
import comfy
from comfy import samplers
import sys

import torch
import torch.nn.functional as F
import torchvision.transforms.v2 as T

import numpy as np
import re

#comfy essentials
def p(image):
    return image.permute([0,3,1,2])
def pb(image):
    return image.permute([0,2,3,1])

# Tensor to PIL (WAS Node)
def tensor2pil(image):
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))

# PIL to Tensor (WAS Node)
def pil2tensor(image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

def make_3d_mask(mask):
    if len(mask.shape) == 4:
        return mask.squeeze(0)

    elif len(mask.shape) == 2:
        return mask.unsqueeze(0)

    return mask

FLOAT = ("FLOAT", {"default": 1,
                   "min": -sys.float_info.max,
                   "max": sys.float_info.max,
                   "step": 0.01})

BOOLEAN = ("BOOLEAN", {"default": True})
BOOLEAN_FALSE = ("BOOLEAN", {"default": False})

INT = ("INT", {"default": 1,
               "min": -sys.maxsize,
               "max": sys.maxsize,
               "step": 1})

STRING = ("STRING", {"default": ""})


class AnyType(str):
    """A special class that is always equal in not equal comparisons. Credit to pythongosssss"""

    def __eq__(self, _) -> bool:
        return True

    def __ne__(self, __value: object) -> bool:
        return False


ANY = AnyType("*")

SCHEDULERS_COMFY = comfy.samplers.KSampler.SCHEDULERS
SCHEDULERS_EFFICIENT = comfy.samplers.KSampler.SCHEDULERS + ['AYS SD1', 'AYS SDXL', 'AYS SVD']
SCHEDULERS_IMPACT = comfy.samplers.KSampler.SCHEDULERS + ['AYS SDXL', 'AYS SD1', 'AYS SVD', 'GITS[coeff=1.2]']
SCHEDULERS_RESTART = ('normal', 'karras', 'exponential', 'sgm_uniform', 'simple', 'ddim_uniform', 'simple_test')

SAMPLERS_COMFY = comfy.samplers.KSampler.SAMPLERS
SAMPLERS_RESTART = ['euler', 'euler_cfg_pp', 'euler_ancestral', 'euler_ancestral_cfg_pp', 'heun', 'heunpp2', 'dpm_2', 'dpm_2_ancestral', 'lms', 'dpmpp_2s_ancestral', 'dpmpp_2m', 'ddpm', 'lcm', 'ipndm', 'ipndm_v', 'deis', 'ddim']

#---------------------------------------------------------------------------------------------------------------------#
#imported from crystools
class CBoolean:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "boolean": BOOLEAN,
            }
        }

    CATEGORY = "Rvaged/Primitives"
    RETURN_TYPES = ("BOOLEAN",)
    RETURN_NAMES = ("boolean",)
    FUNCTION = "execute"

    def execute(self, boolean=True):
        return (boolean,)

#---------------------------------------------------------------------------------------------------------------------#    
class CFloat:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "float": FLOAT,
            }
        }

    CATEGORY = "Rvaged/Primitives"
    RETURN_TYPES = ("FLOAT",)
    RETURN_NAMES = ("float",)
    FUNCTION = "execute"

    def execute(self, float=True):
        return (float,)
    
#---------------------------------------------------------------------------------------------------------------------#    
class CInteger:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "int": INT,
            }
        }

    CATEGORY = "Rvaged/Primitives"
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("int",)
    FUNCTION = "execute"

    def execute(self, int=True):
        return (int,)

#---------------------------------------------------------------------------------------------------------------------#    
class CText:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "string": STRING,
            }
        }

    CATEGORY = "Rvaged/Primitives"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("string",)
    FUNCTION = "execute"

    def execute(self, string=""):
        return (string,)
#---------------------------------------------------------------------------------------------------------------------#
class CTextML:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {"value": ("STRING", {"default": "", "multiline": True})},
        }

    CATEGORY = "Rvaged/Primitives"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("STRING",)
    FUNCTION = "execute"

    def execute(self, value):
        return (value,)
#---------------------------------------------------------------------------------------------------------------------#
def format_datetime(datetime_format):
    today = datetime.now()
    return f"{today.strftime(datetime_format)}"

#---------------------------------------------------------------------------------------------------------------------#
#imported from path-helper
def format_date_time(string, position, datetime_format):
    today = datetime.now()
    if position == "prefix":
        return f"{today.strftime(datetime_format)}_{string}"
    if position == "postfix":
        return f"{string}_{today.strftime(datetime_format)}"

#---------------------------------------------------------------------------------------------------------------------#
def format_variables(string, input_variables):
    if input_variables:
        variables = str(input_variables).split(",")
        return string.format(*variables)
    else:
        return string

#---------------------------------------------------------------------------------------------------------------------#
#altered from CreateRootFolder from path-helper
class CreateProjectFolder:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "date_time_format": ("STRING", {"multiline": False, "default": "%Y-%m-%d"}),
                "add_date_time": (["disable", "prefix", "postfix"],),
                "project_root_name": ("STRING", {"multiline": False, "default": "MyProject"}),
                "create_batch_folder": (["enable", "disable"],),
                "batch_folder_name": ("STRING", {"multiline": False, "default": "batch_{}"}),                
                "output_path_generation": (["relative", "absolute"],)
            },
            "optional": {
                "input_variables": (ANY,)
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "create_project_folder"
    CATEGORY = "Rvaged/Folder"

    def create_project_folder(self, project_root_name, add_date_time, date_time_format, output_path_generation, create_batch_folder, batch_folder_name, input_variables=None):
        mDate = format_datetime(date_time_format)
        new_path = project_root_name

        if add_date_time == "prefix":
            new_path = os.path.join(mDate, project_root_name)
        elif add_date_time == "postfix":
            new_path = os.path.join(project_root_name, mDate)

        if create_batch_folder == "enable":
           folder_name_parsed = format_variables(batch_folder_name, input_variables)
           new_path = os.path.join(new_path, folder_name_parsed)

        if output_path_generation == "relative":
            return ("./" + new_path,)
        elif output_path_generation == "absolute":
            return (os.path.join(self.output_dir, new_path),)
        
#---------------------------------------------------------------------------------------------------------------------#
class Add_Folder:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "path": ("STRING", {"forceInput": True}),
                #"path": ("PATH",),
                "folder_name": ("STRING", {"multiline": False, "default": "SubFolder"})
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("string",)    
    FUNCTION = "add_folder"
    CATEGORY = "Rvaged/Folder"

    def add_folder(self, path, folder_name):
        new_path = os.path.join(path, folder_name)
        return (new_path,)

#---------------------------------------------------------------------------------------------------------------------#
class Add_FileNamePrefix:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "path": ("STRING", {"forceInput": True}),
                #"path": ("PATH",),
                "file_name_prefix": ("STRING", {"multiline": False, "default": "image"}),
                "add_date_time": (["disable", "prefix", "postfix"],),
                "date_time_format": ("STRING", {"multiline": False, "default": "%Y-%m-%d_%H:%M:%S"}),
            },
            "optional": {
                "input_variables": (ANY,)
            }
        }

    CATEGORY = "Rvaged/Folder"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("string",)
    FUNCTION = "add_filename_prefix"

    def add_filename_prefix(self, path, file_name_prefix, add_date_time, date_time_format, input_variables=None):
        filename_name_parsed = format_variables(file_name_prefix, input_variables)
        if add_date_time == "disable":
            new_path = os.path.join(path, filename_name_parsed)
        else:
            new_path = os.path.join(path, format_date_time(filename_name_parsed, add_date_time, date_time_format))
        return (new_path,)

#---------------------------------------------------------------------------------------------------------------------#
class Join_Vars:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "var_1": (ANY,),
            },
            "optional": {
                "var_2": (ANY,),
                "var_3": (ANY,),
                "var_4": (ANY,),
            }
        }

    CATEGORY = "Rvaged/Operation"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("string",)
    FUNCTION = "join_vars"

    def join_vars(self, var_1, var_2=None, var_3=None, var_4=None):
        variables = [var_1, var_2, var_3, var_4]
        return (','.join([str(var) for var in variables if var is not None]),)

#---------------------------------------------------------------------------------------------------------------------#
class Join_Vars_V2:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "var_1": (ANY,),
            },
            "optional": {
                "var_2": (ANY,),
                "var_3": (ANY,),
                "var_4": (ANY,),
                "var_5": (ANY,),
                "var_6": (ANY,),
                "var_7": (ANY,),
                "var_8": (ANY,),
            }
        }

    CATEGORY = "Rvaged/Operation"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("string",)
    FUNCTION = "join_vars2"

    def join_vars2(self, var_1, var_2=None, var_3=None, var_4=None, var_5=None, var_6=None, var_7=None, var_8=None):
        variables = [var_1, var_2, var_3, var_4, var_5, var_6, var_7, var_8]
        return (','.join([str(var) for var in variables if var is not None]),)

#---------------------------------------------------------------------------------------------------------------------#
#imported from ImageSaver
class SamplerSelector:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "sampler_name": (SAMPLERS_COMFY,),
            }
        }

    CATEGORY = "Rvaged/Selector"
    RETURN_TYPES = (SAMPLERS_COMFY,)
    RETURN_NAMES = ("sampler_name",)
    FUNCTION = "get_names"

    def get_names(self, sampler_name):
        return (sampler_name,)
 
#---------------------------------------------------------------------------------------------------------------------#
class SamplerSelectorRestart:
    #restart sampler names: 
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "sampler_name": (SAMPLERS_RESTART,),
            }
        }

    CATEGORY = "Rvaged/Selector"
    RETURN_TYPES = (SAMPLERS_RESTART,)
    RETURN_NAMES = ("sampler_name",)
    FUNCTION = "get_names"

    def get_names(self, sampler_name):
        return (sampler_name,)
 
#---------------------------------------------------------------------------------------------------------------------#
class SchedulerSelector:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "scheduler_comfy": (SCHEDULERS_COMFY,),
                "scheduler_efficient": (SCHEDULERS_EFFICIENT,),
                "scheduler_impact": (SCHEDULERS_IMPACT,),
                "scheduler_restart": (SCHEDULERS_RESTART,),
                }
            }

    CATEGORY = "Rvaged/Selector"
    RETURN_TYPES = (
        SCHEDULERS_COMFY,
        SCHEDULERS_EFFICIENT, 
        SCHEDULERS_IMPACT, 
        SCHEDULERS_RESTART, 
        "STRING",)
    RETURN_NAMES = ("scheduler_comfy", "scheduler_efficient", "scheduler_impact", "scheduler_restart", "scheduler_name",)
    FUNCTION = "get_names"

    def get_names(self, scheduler_comfy, scheduler_efficient, scheduler_impact, scheduler_restart):
        return (scheduler_comfy, scheduler_efficient, scheduler_impact, scheduler_impact, scheduler_restart,)
 #---------------------------------------------------------------------------------------------------------------------#
class SchedulerSelectorComfyUI:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "scheduler_comfy": (SCHEDULERS_COMFY,),
                }
            }

    CATEGORY = "Rvaged/Selector"
    RETURN_TYPES = (SCHEDULERS_COMFY, "STRING",)
    RETURN_NAMES = ("scheduler_comfy", "scheduler_name",)
    FUNCTION = "get_names"

    def get_names(self, scheduler_comfy):
        return (scheduler_comfy,)
#---------------------------------------------------------------------------------------------------------------------#
class SchedulerSelectorEfficient:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "scheduler_efficient": (SCHEDULERS_EFFICIENT,),
                }
            }

    CATEGORY = "Rvaged/Selector"
    RETURN_TYPES = (SCHEDULERS_EFFICIENT, "STRING",)
    RETURN_NAMES = ("scheduler_efficient", "scheduler_name",)
    FUNCTION = "get_names"

    def get_names(self, scheduler_efficient):
        return (scheduler_efficient,)    
#---------------------------------------------------------------------------------------------------------------------#
class SchedulerSelectorImpact:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "scheduler_impact": (SCHEDULERS_IMPACT,),
                }
            }

    CATEGORY = "Rvaged/Selector"
    RETURN_TYPES = (SCHEDULERS_IMPACT, "STRING",)
    RETURN_NAMES = ("scheduler_impact", "scheduler_name",)
    FUNCTION = "get_names"

    def get_names(self, scheduler_impact):
        return (scheduler_impact,)    
#---------------------------------------------------------------------------------------------------------------------#
class SchedulerSelectorRestart:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "scheduler_restart": (SCHEDULERS_RESTART,),
                }
            }

    CATEGORY = "Rvaged/Selector"
    RETURN_TYPES = (SCHEDULERS_RESTART, "STRING",)
    RETURN_NAMES = ("scheduler_restart", "scheduler_name",)
    FUNCTION = "get_names"

    def get_names(self, scheduler_restart):
        return (scheduler_restart,)
    
#---------------------------------------------------------------------------------------------------------------------#
class ClipInputSwitch:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "Input": ("INT", {"default": 1, "min": 1, "max": 2}),
            },
            "optional": {
                "clip1": ("CLIP",),
                "clip2": ("CLIP",),      
            }
        }
    CATEGORY = "Rvaged/Switches"
    RETURN_TYPES = ("CLIP",)
    FUNCTION = "switch"

    def switch(self, Input, clip1=None, clip2=None):
        if Input == 1:
            return (clip1,)
        else:
            return (clip2,)

#---------------------------------------------------------------------------------------------------------------------#
class ConditioningInputSwitch:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "Input": ("INT", {"default": 1, "min": 1, "max": 2}),
            },
            "optional": {
                "conditioning1": ("CONDITIONING",),
                "conditioning2": ("CONDITIONING",),        
            }
        }

    CATEGORY = "Rvaged/Switches"
    RETURN_TYPES = ("CONDITIONING",)
    FUNCTION = "switch"

    def switch(self, Input, conditioning1=None, conditioning2=None):
        if Input == 1:
            return (conditioning1,)
        else:
            return (conditioning2,)

#---------------------------------------------------------------------------------------------------------------------#
#imported from ComfyRoll and used as template for the others
class ImageSwitch:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "Input": ("INT", {"default": 1, "min": 1, "max": 2}),
            },
            "optional": {
                "image1": ("IMAGE",),
                "image2": ("IMAGE",),            
            }
        }

    CATEGORY = "Rvaged/Switches"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "img_switch"

    def img_switch(self, Input, image1=None, image2=None):
        
        if Input == 1:
            return (image1,)
        else:
            return (image2,)

#---------------------------------------------------------------------------------------------------------------------#
class IntegerSwitch:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "Input": ("INT", {"default": 1, "min": 1, "max": 2}),
            },
            "optional": {
                "int1": ("INT", {"forceInput": True}),
                "int2": ("INT", {"forceInput": True}),
            }
        }

    CATEGORY = "Rvaged/Switches"
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("int",)
    FUNCTION = "execute"

    def execute(self, Input, int1=None, int2=None):
        
        if Input == 1:
            return (int1,)
        else:
            return (int2,)

#---------------------------------------------------------------------------------------------------------------------#
class LatentInputSwitch:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "Input": ("INT", {"default": 1, "min": 1, "max": 2}),
            },
            "optional": {
                "latent1": ("LATENT",),
                "latent2": ("LATENT",)          
            }
        }

    CATEGORY = "Rvaged/Switches"
    RETURN_TYPES = ("LATENT",)
    FUNCTION = "switch"

    def switch(self, Input, latent1=None, latent2=None):
        if Input == 1:
            return (latent1,)
        else:
            return (latent2,)

#---------------------------------------------------------------------------------------------------------------------# 
class MaskSwitch:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "Input": ("INT", {"default": 1, "min": 1, "max": 2}),
            },
            "optional": {
                "mask1": ("MASK", {"forceInput": True}),
                "mask2": ("MASK", {"forceInput": True}),
            }
        }

    CATEGORY = "Rvaged/Switches"
    RETURN_TYPES = ("MASK",)
    RETURN_NAMES = ("mask",)
    FUNCTION = "execute"

    def execute(self, Input, mask1=None, mask2=None):
        
        if Input == 1:
            return (mask1,)
        else:
            return (mask2,)

#---------------------------------------------------------------------------------------------------------------------#
class ModelInputSwitch:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "Input": ("INT", {"default": 1, "min": 1, "max": 2}),
            },
            "optional": {
                "model1": ("MODEL",),
                "model2": ("MODEL",),   
            }
        }
    CATEGORY = "Rvaged/Switches"
    RETURN_TYPES = ("MODEL",)
    FUNCTION = "switch"

    def switch(self, Input, model1=None, model2=None):
        if Input == 1:
            return (model1,)
        else:
            return (model2,)

#---------------------------------------------------------------------------------------------------------------------#
class TextInputSwitch:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "Input": ("INT", {"default": 1, "min": 1, "max": 2}),
            },
            "optional": {
                "text1": ("STRING", {"forceInput": True}),
                "text2": ("STRING", {"forceInput": True}), 
            }
        }

    CATEGORY = "Rvaged/Switches"
    RETURN_TYPES = ("STRING",)
    FUNCTION = "switch"

    def switch(self, Input, text1=None, text2=None,):
        if Input == 1:
            return (text1,)
        else:
            return (text2,)

#---------------------------------------------------------------------------------------------------------------------#
class VAEInputSwitch:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "Input": ("INT", {"default": 1, "min": 1, "max": 2}),            
            },
            "optional": {
                "VAE1": ("VAE", {"forceInput": True}),
                "VAE2": ("VAE", {"forceInput": True}),
            }
        }

    CATEGORY = "Rvaged/Switches"
    RETURN_TYPES = ("VAE",)   
    FUNCTION = "switch"

    def switch(self, Input, VAE1=None, VAE2=None,):
        if Input == 1:
            return (VAE1,)
        else:
            return (VAE2,)

#---------------------------------------------------------------------------------------------------------------------#
class AUDIOInputSwitch:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "Input": ("INT", {"default": 1, "min": 1, "max": 2}),            
            },
            "optional": {
                "audio1": ("AUDIO", {"forceInput": True}),
                "audio2": ("AUDIO", {"forceInput": True}),
            }
        }

    CATEGORY = "Rvaged/Switches"
    RETURN_TYPES = ("AUDIO",)   
    FUNCTION = "switch"

    def switch(self, Input, audio1=None, audio2=None,):
        if Input == 1:
            return (audio1,)
        else:
            return (audio2,)

#---------------------------------------------------------------------------------------------------------------------#
# IMAGES TO RGB (WAS Node)
class Images2RGB:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
            },
        }

    CATEGORY = "Rvaged/Conversion"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "Images_to_RGB"

    def Images_to_RGB(self, images):

        if len(images) > 1:
            tensors = []
            for image in images:
                tensors.append(pil2tensor(tensor2pil(image).convert('RGB')))
            tensors = torch.cat(tensors, dim=0)
            return (tensors, )
        else:
            return (pil2tensor(tensor2pil(images).convert("RGB")), )

#---------------------------------------------------------------------------------------------------------------------#        
#from comfy essentials
class ImageList2Batch:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
            }
        }

    CATEGORY = "Rvaged/Conversion"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "ImageList_to_Batch"
    INPUT_IS_LIST = True

    def ImageList_to_Batch(self, images):
        shape = images[0].shape[1:3]
        out = []

        for i in range(len(images)):
            img = p(images[i])
            if images[i].shape[1:3] != shape:
                transforms = T.Compose([
                    T.CenterCrop(min(img.shape[2], img.shape[3])),
                    T.Resize((shape[0], shape[1]), interpolation=T.InterpolationMode.BICUBIC),
                ])
                img = transforms(img)
            out.append(pb(img))
            #image[i] = pb(transforms(img))

        out = torch.cat(out, dim=0)

        return (out,)        

#---------------------------------------------------------------------------------------------------------------------#
#from impact
class ImageBatch2List:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"images": ("IMAGE",), }}

    CATEGORY = "Rvaged/Conversion"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "ImageBatch_to_List"

    def ImageBatch_to_List(self, images):
        iimages = [images[i:i + 1, ...] for i in range(images.shape[0])]
        return (iimages, )

#---------------------------------------------------------------------------------------------------------------------#
class MaskBatch2List:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
                        "masks": ("MASK", ),
                      }
                }

    CATEGORY = "Rvaged/Conversion"
    RETURN_TYPES = ("MASK", )
    OUTPUT_IS_LIST = (True, )
    FUNCTION = "MaskBatch_to_List"

    def MaskBatch_to_List(self, masks):
        if masks is None:
            empty_mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
            return ([empty_mask], )

        res = []

        for mask in masks:
            res.append(mask)

        print(f"mask len: {len(res)}")

        res = [make_3d_mask(x) for x in res]

        return (res, )

#---------------------------------------------------------------------------------------------------------------------#
class MaskList2Batch:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
                        "mask": ("MASK", ),
                      }
                }

    INPUT_IS_LIST = True

    CATEGORY = "Rvaged/Conversion"
    RETURN_TYPES = ("MASK", )
    FUNCTION = "MaskList_to_Batch"

    def MaskList_to_Batch(self, mask):
        if len(mask) == 1:
            mask = make_3d_mask(mask[0])
            return (mask,)
        elif len(mask) > 1:
            mask1 = make_3d_mask(mask[0])

            for mask2 in mask[1:]:
                mask2 = make_3d_mask(mask2)
                if mask1.shape[1:] != mask2.shape[1:]:
                    mask2 = comfy.utils.common_upscale(mask2.movedim(-1, 1), mask1.shape[2], mask1.shape[1], "lanczos", "center").movedim(1, -1)
                mask1 = torch.cat((mask1, mask2), dim=0)

            return (mask1,)
        else:
            empty_mask = torch.zeros((1, 64, 64), dtype=torch.float32, device="cpu").unsqueeze(0)
            return (empty_mask,)

#---------------------------------------------------------------------------------------------------------------------#  
# from logic  
class IfExecute:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "ANY": (ANY,),
                "IF_TRUE": (ANY,),
                "IF_FALSE": (ANY,),
            },
        }

    CATEGORY = "Rvaged/Operation"
    RETURN_TYPES = (ANY,)
    RETURN_NAMES = "?"
    FUNCTION = "return_based_on_bool"

    def return_based_on_bool(self, ANY, IF_TRUE, IF_FALSE):
        return (IF_TRUE if ANY else IF_FALSE,)

#---------------------------------------------------------------------------------------------------------------------#
#from Logic-Utils
class ReplaceString:
    @classmethod
    def INPUT_TYPES(s):
        return {
        "required": {
            "String": ("STRING", {"default": ""}),
            "Regex": ("STRING", {"default": ""}),
            "ReplaceWith": ("STRING", {"default": ""}),
        }
    }
    
    CATEGORY = "Rvaged/Operation"
    RETURN_TYPES = ("STRING",)
    FUNCTION = "replace_string"
    
    def replace_string(self, String, Regex, ReplaceWith):
        # using regex
        return (re.sub(Regex, ReplaceWith, String),)

#---------------------------------------------------------------------------------------------------------------------#
class MergeString:
    @classmethod
    def INPUT_TYPES(s):
        return {
        "required": {
            "input1": (ANY, {"default": ""}),
            "input2": (ANY, {"default": ""}),
        }
    }
    CATEGORY = "Rvaged/Operation"
    RETURN_TYPES = ("STRING",)
    FUNCTION = "merge_string"
    
    def merge_string(self, input1, input2):
        return (str(input1) + str(input2),)

#---------------------------------------------------------------------------------------------------------------------#
class PassAudio:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "audio": ("AUDIO",),
            },
        }
    
    CATEGORY = "Rvaged/Passer"
    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "passthrough"

    def passthrough(self, audio):
        return audio,

#---------------------------------------------------------------------------------------------------------------------#
class PassClip:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "clip": ("CLIP",),
            },
        }
    
    CATEGORY = "Rvaged/Passer"
    RETURN_TYPES = ("CLIP",)
    FUNCTION = "passthrough"

    def passthrough(self, clip):
        return clip,

#---------------------------------------------------------------------------------------------------------------------#
class PassImages:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
            },
        }
    
    CATEGORY = "Rvaged/Passer"
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "passthrough"

    def passthrough(self, image):
        return image,

#---------------------------------------------------------------------------------------------------------------------#
class PassLatent:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "latent": ("LATENT",),
            },
        }
    
    CATEGORY = "Rvaged/Passer"
    RETURN_TYPES = ("LATENT",)
    FUNCTION = "passthrough"

    def passthrough(self, latent):
        return latent,

#---------------------------------------------------------------------------------------------------------------------#
class PassMasks:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "mask": ("MASK",),
            },
        }
    
    CATEGORY = "Rvaged/Passer"
    RETURN_TYPES = ("MASK",)
    FUNCTION = "passthrough"

    def passthrough(self, mask):
        return mask,

#---------------------------------------------------------------------------------------------------------------------#
class PassModel:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
            },
        }
    
    CATEGORY = "Rvaged/Passer"
    RETURN_TYPES = ("MODEL",)
    FUNCTION = "passthrough"

    def passthrough(self, model):
        return model,
#---------------------------------------------------------------------------------------------------------------------------------------------------#
# Cloned from Mikey Nodes
class Int2Str:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"int_": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "forceInput": True}),
                }
        }

    CATEGORY = ("Rvaged/Conversion")
    RETURN_TYPES = ("STRING", )
    RETURN_NAMES = ("STRING", )
    FUNCTION = 'convert'

    def convert(self, int_):
        return (f'{int_}',)

#---------------------------------------------------------------------------------------------------------------------------------------------------#
# based on Mikey Nodes
class Float2Str:

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"float_": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1000000.0, "forceInput": True}),
                }        
        }

    CATEGORY = ("Rvaged/Conversion")
    RETURN_TYPES = ('STRING',)
    RETURN_NAMES = ('STRING',)
    FUNCTION = 'convert'

    def convert(self, float_):
        return (f'{float_}',)

#---------------------------------------------------------------------------------------------------------------------
# based on Mikey Nodes
class Float2Int:

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"_float": ("FLOAT", {"default": 0.0, "forceInput": True, "forceInput": True}),
                }
        }

    CATEGORY = ("Rvaged/Conversion")
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("INT",)
    FUNCTION = "convert"

    def convert(self, _float):
        return (int(_float),)
#---------------------------------------------------------------------------------------------------------------------#    
class IntValueGrp:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "Width": ("INT", {"default": 150}),
                "Height": ("INT", {"default": 20}),
            },
            "optional": {
                "Offset_Y": ("INT",{"default": 0}),
                "Offset_X": ("INT",{"default": 0}),
            }
        }

    CATEGORY = "Rvaged"
    RETURN_TYPES = ("INT","INT","INT","INT",)
    RETURN_NAMES = ("width","height","offset_y","offset_x",)
    FUNCTION = "execute"

    def execute(self, Width, Height, Offset_Y, Offset_X):
        return (Width,Height,Offset_Y,Offset_X,)

#---------------------------------------------------------------------------------------------------------------------#