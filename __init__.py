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

from .nodes import *

NODE_CLASS_MAPPINGS = {
    "Create Project Folder": CreateProjectFolder,
    "Add Folder": Add_Folder,
    "Add File Name Prefix": Add_FileNamePrefix,
    "Join Variables": Join_Vars,
    "Sampler Selector": SamplerSelector, 
    "Scheduler Selector": SchedulerSelector, 
    "Image Switch": ImageSwitch, 
    "Integer Switch": IntegerSwitch, 
    "Mask Switch": MaskSwitch, 
    "Latent Switch": LatentInputSwitch, 
    "Conditioning Switch": ConditioningInputSwitch, 
    "Clip Switch": ClipInputSwitch, 
    "Model Switch": ModelInputSwitch, 
    "Text Switch": TextInputSwitch, 
    "VAE Switch": VAEInputSwitch, 
    "Boolean": CBoolean, 
    "Float": CFloat, 
    "Integer": CInteger, 
    "String": CText, 
    "Imagelist2Batch": ImageList2Batch, 
    "ImageBatch2List": ImageBatch2List,
    "Images2RGB": Images2RGB,
}
