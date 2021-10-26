# Requirements:
#   - fmtc
#   - nnedi3
# From:
#   - https://github.com/mawen1250/VapourSynth-script
#   - https://github.com/HomeOfVapourSynthEvolution/mvsfunc
import vapoursynth as vs
import math

def SetColorSpace(clip, ChromaLocation=None, ColorRange=None, Primaries=None, Matrix=None, Transfer=None):
    # Set VS core and function name
    core = vs.core
    funcName = 'SetColorSpace'
    
    if not isinstance(clip, vs.VideoNode):
        raise TypeError(funcName + ': \"clip\" must be a clip!')
    
    # Modify frame properties
    if ChromaLocation is None:
        pass
    elif isinstance(ChromaLocation, bool):
        if ChromaLocation is False:
            clip = core.std.SetFrameProp(clip, prop='_ChromaLocation', delete=True)
    elif isinstance(ChromaLocation, int):
        if ChromaLocation >= 0 and ChromaLocation <=5:
            clip = core.std.SetFrameProp(clip, prop='_ChromaLocation', intval=ChromaLocation)
        else:
            raise ValueError(funcName + ': valid range of \"ChromaLocation\" is [0, 5]!')
    else:
        raise TypeError(funcName + ': \"ChromaLocation\" must be an int or a bool!')
    
    if ColorRange is None:
        pass
    elif isinstance(ColorRange, bool):
        if ColorRange is False:
            clip = core.std.SetFrameProp(clip, prop='_ColorRange', delete=True)
    elif isinstance(ColorRange, int):
        if ColorRange >= 0 and ColorRange <=1:
            clip = core.std.SetFrameProp(clip, prop='_ColorRange', intval=ColorRange)
        else:
            raise ValueError(funcName + ': valid range of \"ColorRange\" is [0, 1]!')
    else:
        raise TypeError(funcName + ': \"ColorRange\" must be an int or a bool!')
    
    if Primaries is None:
        pass
    elif isinstance(Primaries, bool):
        if Primaries is False:
            clip = core.std.SetFrameProp(clip, prop='_Primaries', delete=True)
    elif isinstance(Primaries, int):
        clip = core.std.SetFrameProp(clip, prop='_Primaries', intval=Primaries)
    else:
        raise TypeError(funcName + ': \"Primaries\" must be an int or a bool!')
    
    if Matrix is None:
        pass
    elif isinstance(Matrix, bool):
        if Matrix is False:
            clip = core.std.SetFrameProp(clip, prop='_Matrix', delete=True)
    elif isinstance(Matrix, int):
        clip = core.std.SetFrameProp(clip, prop='_Matrix', intval=Matrix)
    else:
        raise TypeError(funcName + ': \"Matrix\" must be an int or a bool!')
    
    if Transfer is None:
        pass
    elif isinstance(Transfer, bool):
        if Transfer is False:
            clip = core.std.SetFrameProp(clip, prop='_Transfer', delete=True)
    elif isinstance(Transfer, int):
        clip = core.std.SetFrameProp(clip, prop='_Transfer', intval=Transfer)
    else:
        raise TypeError(funcName + ': \"Transfer\" must be an int or a bool!')
    
    # Output
    return clip

def _quantization_parameters(sample=None, depth=None, full=None, chroma=None, funcName='_quantization_parameters'):
    qp = {}
    
    if sample is None:
        sample = vs.INTEGER
    if depth is None:
        depth = 8
    elif depth < 1:
        raise ValueError(funcName + ': \"depth\" should not be less than 1!')
    if full is None:
        full = True
    if chroma is None:
        chroma = False
    
    lShift = depth - 8
    rShift = 8 - depth
    
    if sample == vs.INTEGER:
        if chroma:
            qp['floor'] = 0 if full else 16 << lShift if lShift >= 0 else 16 >> rShift
            qp['neutral'] = 128 << lShift if lShift >= 0 else 128 >> rShift
            qp['ceil'] = (1 << depth) - 1 if full else 240 << lShift if lShift >= 0 else 240 >> rShift
            qp['range'] = qp['ceil'] - qp['floor']
        else:
            qp['floor'] = 0 if full else 16 << lShift if lShift >= 0 else 16 >> rShift
            qp['neutral'] = qp['floor']
            qp['ceil'] = (1 << depth) - 1 if full else 235 << lShift if lShift >= 0 else 235 >> rShift
            qp['range'] = qp['ceil'] - qp['floor']
    elif sample == vs.FLOAT:
        if chroma:
            qp['floor'] = -0.5
            qp['neutral'] = 0.0
            qp['ceil'] = 0.5
            qp['range'] = qp['ceil'] - qp['floor']
        else:
            qp['floor'] = 0.0
            qp['neutral'] = qp['floor']
            qp['ceil'] = 1.0
            qp['range'] = qp['ceil'] - qp['floor']
    else:
        raise ValueError(funcName + ': Unsupported \"sample\" specified!')
    
    return qp

def _quantization_conversion(clip, depths=None, depthd=None, sample=None, fulls=None, fulld=None, chroma=None,\
clamp=None, dbitPS=None, mode=None, funcName='_quantization_conversion'):
    # Set VS core and function name
    core = vs.core
    
    if not isinstance(clip, vs.VideoNode):
        raise TypeError(funcName + ': \"clip\" must be a clip!')
    
    # Get properties of input clip
    sFormat = clip.format
    
    sColorFamily = sFormat.color_family
    sIsRGB = sColorFamily == vs.RGB
    sIsYUV = sColorFamily == vs.YUV
    sIsGRAY = sColorFamily == vs.GRAY
    sIsYCOCG = sColorFamily == vs.YCOCG
    if sColorFamily == vs.COMPAT:
        raise ValueError(funcName + ': color family *COMPAT* is not supported!')
    
    sbitPS = sFormat.bits_per_sample
    sSType = sFormat.sample_type
    
    if depths is None:
        depths = sbitPS
    elif not isinstance(depths, int):
        raise TypeError(funcName + ': \"depths\" must be an int!')
    
    if fulls is None:
        # If not set, assume limited range for YUV and Gray input
        fulls = False if sIsYUV or sIsGRAY else True
    elif not isinstance(fulls, int):
        raise TypeError(funcName + ': \"fulls\" must be a bool!')
    
    if chroma is None:
        chroma = False
    elif not isinstance(chroma, int):
        raise TypeError(funcName + ': \"chroma\" must be a bool!')
    elif not sIsGRAY:
        chroma = False
    
    # Get properties of output clip
    if depthd is None:
        pass
    elif not isinstance(depthd, int):
        raise TypeError(funcName + ': \"depthd\" must be an int!')
    if sample is None:
        if depthd is None:
            dSType = sSType
            depthd = depths
        else:
            dSType = vs.FLOAT if dbitPS >= 32 else vs.INTEGER
    elif not isinstance(sample, int):
        raise TypeError(funcName + ': \"sample\" must be an int!')
    elif sample != vs.INTEGER and sample != vs.FLOAT:
        raise ValueError(funcName + ': \"sample\" must be either 0(vs.INTEGER) or 1(vs.FLOAT)!')
    else:
        dSType = sample
    if dSType == vs.INTEGER and (dbitPS < 1 or dbitPS > 16):
        raise ValueError(funcName + ': {0}-bit integer output is not supported!'.format(dbitPS))
    if dSType == vs.FLOAT and (dbitPS != 16 and dbitPS != 32):
        raise ValueError(funcName + ': {0}-bit float output is not supported!'.format(dbitPS))
    
    if fulld is None:
        fulld = fulls
    elif not isinstance(fulld, int):
        raise TypeError(funcName + ': \"fulld\" must be a bool!')
    
    if clamp is None:
        clamp = dSType == vs.INTEGER
    elif not isinstance(clamp, int):
        raise TypeError(funcName + ': \"clamp\" must be a bool!')
    
    if dbitPS is None:
        if depthd < 8:
            dbitPS = 8
        else:
            dbitPS = depthd
    elif not isinstance(dbitPS, int):
        raise TypeError(funcName + ': \"dbitPS\" must be an int!')
    
    if mode is None:
        mode = 0
    elif not isinstance(mode, int):
        raise TypeError(funcName + ': \"mode\" must be an int!')
    elif depthd >= 8:
        mode = 0
    
    dFormat = core.register_format(sFormat.color_family, dSType, dbitPS, sFormat.subsampling_w, sFormat.subsampling_h)
    
    # Expression function
    def gen_expr(chroma, mode):
        if dSType == vs.INTEGER:
            exprLower = 0
            exprUpper = 1 << (dFormat.bytes_per_sample * 8) - 1
        else:
            exprLower = float('-inf')
            exprUpper = float('inf')
        
        sQP = _quantization_parameters(sSType, depths, fulls, chroma, funcName)
        dQP = _quantization_parameters(dSType, depthd, fulld, chroma, funcName)
        
        gain = dQP['range'] / sQP['range']
        offset = dQP['neutral' if chroma else 'floor'] - sQP['neutral' if chroma else 'floor'] * gain
        
        if mode == 1:
            scale = 256
            gain = gain * scale
            offset = offset * scale
        else:
            scale = 1
        
        if gain != 1 or offset != 0 or clamp:
            expr = " x "
            if gain != 1: expr = expr + " {} * ".format(gain)
            if offset != 0: expr = expr + " {} + ".format(offset)
            if clamp:
                if dQP['floor'] * scale > exprLower: expr = expr + " {} max ".format(dQP['floor'] * scale)
                if dQP['ceil'] * scale < exprUpper: expr = expr + " {} min ".format(dQP['ceil'] * scale)
        else:
            expr = ""
        
        return expr
    
    # Process
    Yexpr = gen_expr(False, mode)
    Cexpr = gen_expr(True, mode)
    
    if sIsYUV or sIsYCOCG:
        expr = [Yexpr, Cexpr]
    elif sIsGRAY and chroma:
        expr = Cexpr
    else:
        expr = Yexpr
    
    clip = core.std.Expr(clip, expr, format=dFormat.id)
    
    # Output
    clip = SetColorSpace(clip, ColorRange=0 if fulld else 1)
    return clip

def zDepth(clip, sample=None, depth=None, range=None, range_in=None, dither_type=None, cpu_type=None, prefer_props=None):
    # Set VS core and function name
    core = vs.core
    funcName = 'zDepth'
    
    if not isinstance(clip, vs.VideoNode):
        raise TypeError(funcName + ': \"clip\" must be a clip!')
    
    # Get properties of input clip
    sFormat = clip.format
    
    # Get properties of output clip
    if sample is None:
        sample = sFormat.sample_type
    elif not isinstance(sample, int):
        raise TypeError(funcName + ': \"sample\" must be an int!')
    
    if depth is None:
        depth = sFormat.bits_per_sample
    elif not isinstance(depth, int):
        raise TypeError(funcName + ': \"depth\" must be an int!')
    
    format = core.register_format(sFormat.color_family, sample, depth, sFormat.subsampling_w, sFormat.subsampling_h)
    
    # Process
    zimgResize = core.version_number() >= 29
    zimgPlugin = core.get_plugins().__contains__('the.weather.channel')
    if zimgResize:
        clip = core.resize.Bicubic(clip, format=format.id, range=range, range_in=range_in, dither_type=dither_type, prefer_props=prefer_props)
    elif zimgPlugin and core.z.get_functions().__contains__('Format'):
        clip = core.z.Format(clip, format=format.id, range=range, range_in=range_in, dither_type=dither_type, cpu_type=cpu_type)
    elif zimgPlugin and core.z.get_functions().__contains__('Depth'):
        clip = core.z.Depth(clip, dither=dither_type, sample=sample, depth=depth, fullrange_in=range_in, fullrange_out=range)
    else:
        raise AttributeError(funcName + ': Available zimg not found!')
    
    # Output
    return clip

def Depth(input, depth=None, sample=None, fulls=None, fulld=None, \
dither=None, useZ=None, prefer_props=None, ampo=None, ampn=None, dyn=None, staticnoise=None):
    # Set VS core and function name
    core = vs.core
    funcName = 'Depth'
    clip = input
    
    if not isinstance(input, vs.VideoNode):
        raise TypeError(funcName + ': \"input\" must be a clip!')
    
    prefer_props_range = None
    
    # Get properties of input clip
    sFormat = input.format
    
    sColorFamily = sFormat.color_family
    sIsRGB = sColorFamily == vs.RGB
    sIsYUV = sColorFamily == vs.YUV
    sIsGRAY = sColorFamily == vs.GRAY
    sIsYCOCG = sColorFamily == vs.YCOCG
    if sColorFamily == vs.COMPAT:
        raise ValueError(funcName + ': color family *COMPAT* is not supported!')
    
    sbitPS = sFormat.bits_per_sample
    sSType = sFormat.sample_type
    
    if fulls is None:
        # If not set, assume limited range for YUV and Gray input
        fulls = False if sIsYUV or sIsGRAY else True
    elif not isinstance(fulls, int):
        raise TypeError(funcName + ': \"fulls\" must be a bool!')
    
    # Get properties of output clip
    lowDepth = False
    
    if depth is None:
        dbitPS = sbitPS
    elif not isinstance(depth, int):
        raise TypeError(funcName + ': \"depth\" must be an int!')
    else:
        if depth < 8:
            dbitPS = 8
            lowDepth = True
        else:
            dbitPS = depth
    if sample is None:
        if depth is None:
            dSType = sSType
            depth = dbitPS
        else:
            dSType = vs.FLOAT if dbitPS >= 32 else vs.INTEGER
    elif not isinstance(sample, int):
        raise TypeError(funcName + ': \"sample\" must be an int!')
    elif sample != vs.INTEGER and sample != vs.FLOAT:
        raise ValueError(funcName + ': \"sample\" must be either 0(vs.INTEGER) or 1(vs.FLOAT)!')
    else:
        dSType = sample
    if depth is None and sSType != vs.FLOAT and sample == vs.FLOAT:
        dbitPS = 32
    elif depth is None and sSType != vs.INTEGER and sample == vs.INTEGER:
        dbitPS = 16
    if dSType == vs.INTEGER and (dbitPS < 1 or dbitPS > 16):
        raise ValueError(funcName + ': {0}-bit integer output is not supported!'.format(dbitPS))
    if dSType == vs.FLOAT and (dbitPS != 16 and dbitPS != 32):
        raise ValueError(funcName + ': {0}-bit float output is not supported!'.format(dbitPS))
    
    if fulld is None:
        fulld = fulls
    elif not isinstance(fulld, int):
        raise TypeError(funcName + ': \"fulld\" must be a bool!')
    
    # Low-depth support
    if lowDepth:
        if dither == "none" or dither == 1:
            clip = _quantization_conversion(clip, sbitPS, depth, vs.INTEGER, fulls, fulld, False, False, 8, 0, funcName)
            clip = _quantization_conversion(clip, depth, 8, vs.INTEGER, fulld, fulld, False, False, 8, 0, funcName)
            return clip
        else:
            full = fulld
            clip = _quantization_conversion(clip, sbitPS, depth, vs.INTEGER, fulls, full, False, False, 16, 1, funcName)
            sSType = vs.INTEGER
            sbitPS = 16
            fulls = False
            fulld = False
    
    # Whether to use zDepth or fmtc.bitdepth for conversion
    # When 13-,15-bit integer or 16-bit float format is involved, force using zDepth
    if useZ is None:
        useZ = False
    elif not isinstance(useZ, int):
        raise TypeError(funcName + ': \"useZ\" must be a bool!')
    if sSType == vs.INTEGER and (sbitPS == 13 or sbitPS == 15):
        useZ = True
    if dSType == vs.INTEGER and (dbitPS == 13 or dbitPS == 15):
        useZ = True
    if (sSType == vs.FLOAT and sbitPS < 32) or (dSType == vs.FLOAT and dbitPS < 32):
        useZ = True
    
    if prefer_props is None:
        prefer_props = False
    elif not isinstance(prefer_props, int):
        raise TypeError(funcName + ': \"prefer_props\" must be a bool!')
    if prefer_props_range is None:
        prefer_props_range = prefer_props
    
    # Dithering type
    if ampn is not None and not isinstance(ampn, float) and not isinstance(ampn, int):
            raise TypeError(funcName + ': \"ampn\" must be an int or a float!')
    
    if dither is None:
        if dbitPS == 32 or (dbitPS >= sbitPS and fulld == fulls and fulld == False):
            dither = "none" if useZ else 1
        else:
            dither = "error_diffusion" if useZ else 3
    elif not isinstance(dither, int) and not isinstance(dither, str):
        raise TypeError(funcName + ': \"dither\" must be an int or a str!')
    else:
        if isinstance(dither, str):
            dither = dither.lower()
            if dither != "none" and dither != "ordered" and dither != "random" and dither != "error_diffusion":
                raise ValueError(funcName + ': Unsupported \"dither\" specified!')
        else:
            if dither < 0 or dither > 7:
                raise ValueError(funcName + ': Unsupported \"dither\" specified!')
        if useZ and isinstance(dither, int):
            if dither == 0:
                dither = "ordered"
            elif dither == 1 or dither == 2:
                if ampn is not None and ampn > 0:
                    dither = "random"
                else:
                    dither = "none"
            else:
                dither = "error_diffusion"
        elif not useZ and isinstance(dither, str):
            if dither == "none":
                dither = 1
            elif dither == "ordered":
                dither = 0
            elif dither == "random":
                if ampn is None:
                    dither = 1
                    ampn = 1
                elif ampn > 0:
                    dither = 1
                else:
                    dither = 3
            else:
                dither = 3
    
    if not useZ:
        if ampo is None:
            ampo = 1.5 if dither == 0 else 1
        elif not isinstance(ampo, float) and not isinstance(ampo, int):
            raise TypeError(funcName + ': \"ampo\" must be an int or a float!')
    
    # Skip processing if not needed
    if dSType == sSType and dbitPS == sbitPS and (sSType == vs.FLOAT or (fulld == fulls and not prefer_props_range)) and not lowDepth:
        return clip
    
    # Apply conversion
    if useZ:
        clip = zDepth(clip, sample=dSType, depth=dbitPS, range=fulld, range_in=fulls, dither_type=dither, prefer_props=prefer_props_range)
    else:
        clip = core.fmtc.bitdepth(clip, bits=dbitPS, flt=dSType, fulls=fulls, fulld=fulld, dmode=dither, ampo=ampo, ampn=ampn, dyn=dyn, staticnoise=staticnoise)
        clip = SetColorSpace(clip, ColorRange=0 if fulld else 1)
    
    # Low-depth support
    if lowDepth:
        clip = _quantization_conversion(clip, depth, 8, vs.INTEGER, full, full, False, False, 8, 0, funcName)
    
    # Output
    return clip

def nnedi3_resample(input, target_width=None, target_height=None, src_left=None, src_top=None, src_width=None, src_height=None, csp=None, mats=None, matd=None, cplaces=None, cplaced=None, fulls=None, fulld=None, curves=None, curved=None, sigmoid=None, scale_thr=None, nsize=None, nns=None, qual=None, etype=None, pscrn=None, opt=None, int16_prescreener=None, int16_predictor=None, exp=None, kernel=None, invks=False, taps=None, invkstaps=3, a1=None, a2=None, chromak_up=None, chromak_up_taps=None, chromak_up_a1=None, chromak_up_a2=None, chromak_down=None, chromak_down_invks=False, chromak_down_invkstaps=3, chromak_down_taps=None, chromak_down_a1=None, chromak_down_a2=None):
    core = vs.core
    funcName = 'nnedi3_resample'
    
    # Get property about input clip
    if not isinstance(input, vs.VideoNode):
        raise TypeError(funcName + ': This is not a clip!')
    
    sFormat = input.format
    
    sColorFamily = sFormat.color_family
    if sColorFamily == vs.COMPAT:
        raise ValueError(funcName + ': Color family *COMPAT* of input clip is not supported!')
    sIsGRAY = sColorFamily == vs.GRAY
    sIsYUV = sColorFamily == vs.YUV or sColorFamily == vs.YCOCG
    sIsRGB = sColorFamily == vs.RGB
    
    sbitPS = sFormat.bits_per_sample
    
    sHSubS = 1 << sFormat.subsampling_w
    sVSubS = 1 << sFormat.subsampling_h
    sIsSubS = sHSubS > 1 or sVSubS > 1
    
    sPlaneNum = sFormat.num_planes
    
    # Get property about output clip
    dFormat = sFormat if csp is None else core.get_format(csp)
    
    dColorFamily = dFormat.color_family
    if dColorFamily == vs.COMPAT:
        raise ValueError(funcName + ': Color family *COMPAT* of output clip is not supported!')
    dIsGRAY = dColorFamily == vs.GRAY
    dIsYUV = dColorFamily == vs.YUV or dColorFamily == vs.YCOCG
    dIsRGB = dColorFamily == vs.RGB
    
    dbitPS = dFormat.bits_per_sample
    
    dHSubS = 1 << dFormat.subsampling_w
    dVSubS = 1 << dFormat.subsampling_h
    dIsSubS = dHSubS > 1 or dVSubS > 1
    
    dPlaneNum = dFormat.num_planes
    
    # Parameters of format
    SD = input.width <= 1024 and input.height <= 576
    HD = input.width <= 2048 and input.height <= 1536
    
    if mats is None:
        mats = "601" if SD else "709" if HD else "2020"
    else:
        mats = mats.lower()
    if matd is None:
        matd = mats
    else:
        matd = matd.lower()
        # Matrix of output clip makes sense only if dst is not of RGB
        if dIsRGB:
            matd = mats
        # Matrix of input clip makes sense only src is not of GRAY or RGB
        if sIsGRAY or sIsRGB:
            mats = matd
    if cplaces is None:
        if sHSubS == 4:
            cplaces = 'dv'
        else:
            cplaces = 'mpeg2'
    else:
        cplaces = cplaces.lower()
    if cplaced is None:
        if dHSubS == 4:
            cplaced = 'dv'
        else:
            cplaced = cplaces
    else:
        cplaced = cplaced.lower()
    if fulls is None:
        fulls = sColorFamily == vs.YCOCG or sColorFamily == vs.RGB
    if fulld is None:
        if dColorFamily == sColorFamily:
            fulld = fulls
        else:
            fulld = dColorFamily == vs.YCOCG or dColorFamily == vs.RGB
    if curves is None:
        curves = 'linear'
    else:
        curves = curves.lower()
    if curved is None:
        curved = curves
    else:
        curved = curved.lower()
    if sigmoid is None:
        sigmoid = False
    
    # Parameters of scaling
    if target_width is None:
        target_width = input.width
    if target_height is None:
        target_height = input.height
    if src_left is None:
        src_left = 0
    if src_top is None:
        src_top = 0
    if src_width is None:
        src_width = input.width
    elif src_width <= 0:
        src_width = input.width - src_left + src_width
    if src_height is None:
        src_height = input.height
    elif src_height <= 0:
        src_height = input.height - src_top + src_height
    if scale_thr is None:
        scale_thr = 1.125
    
    src_right = src_width - input.width + src_left
    src_bottom = src_height - input.height + src_top
    
    hScale = target_width / src_width
    vScale = target_height / src_height
    
    # Parameters of nnedi3
    if nsize is None:
        nsize = 0
    if nns is None:
        nns = 3
    if qual is None:
        qual = 2
    
    # Parameters of fmtc.resample
    if kernel is None:
        if not invks:
            kernel = 'spline36'
        else:
            kernel = 'bilinear'
    else:
        kernel = kernel.lower()
    if chromak_up is None:
        chromak_up = 'nnedi3'
    else:
        chromak_up = chromak_up.lower()
    if chromak_up == 'softcubic':
        chromak_up = 'bicubic'
        if chromak_up_a1 is None:
            chromak_up_a1 = 75
        chromak_up_a1 = chromak_up_a1 / 100
        chromak_up_a2 = 1 - chromak_up_a1
    if chromak_down is None:
        chromak_down = 'bicubic'
    else:
        chromak_down = chromak_down.lower()
    if chromak_down == 'softcubic':
        chromak_down = 'bicubic'
        if chromak_down_a1 is None:
            chromak_down_a1 = 75
        chromak_down_a1 = chromak_down_a1 / 100
        chromak_down_a2 = 1 - chromak_down_a1
    
    # Procedure decision
    hIsScale = hScale != 1
    vIsScale = vScale != 1
    isScale = hIsScale or vIsScale
    hResample = hIsScale or int(src_left) != src_left or int(src_right) != src_right
    vResample = vIsScale or int(src_top) != src_top or int(src_bottom) != src_bottom
    resample = hResample or vResample
    hReSubS = dHSubS != sHSubS
    vReSubS = dVSubS != sVSubS
    reSubS = hReSubS or vReSubS
    sigmoid = sigmoid and resample
    sGammaConv = curves != 'linear'
    dGammaConv = curved != 'linear'
    gammaConv = (sGammaConv or dGammaConv or sigmoid) and (resample or curved != curves)
    scaleInGRAY = sIsGRAY or dIsGRAY
    scaleInYUV = not scaleInGRAY and mats == matd and not gammaConv and (reSubS or (sIsYUV and dIsYUV))
    scaleInRGB = not scaleInGRAY and not scaleInYUV
    # If matrix conversion or gamma correction is applied, scaling will be done in RGB. Otherwise, if at least one of input&output clip is RGB and no chroma subsampling is involved, scaling will be done in RGB.
    
    # Chroma placement relative to the frame center in luma scale
    sCLeftAlign = cplaces == 'mpeg2' or cplaces == 'dv'
    sHCPlace = 0 if not sCLeftAlign else 0.5 - sHSubS / 2
    sVCPlace = 0
    dCLeftAlign = cplaced == 'mpeg2' or cplaced == 'dv'
    dHCPlace = 0 if not dCLeftAlign else 0.5 - dHSubS / 2
    dVCPlace = 0
    
    # Convert depth to 16-bit
    last = Depth(input, depth=16, fulls=fulls)
    
    # Color space conversion before scaling
    if scaleInGRAY and sIsYUV:
        if mats != matd:
            last = core.fmtc.matrix(last, mats=mats, matd=matd, fulls=fulls, fulld=fulld, col_fam=vs.GRAY, singleout=0)
        last = core.std.ShufflePlanes(last, [0], vs.GRAY)
    elif scaleInGRAY and sIsRGB:
        # Matrix conversion for output clip of GRAY
        last = core.fmtc.matrix(last, mat=matd, fulls=fulls, fulld=fulld, col_fam=vs.GRAY, singleout=0)
        fulls = fulld
    elif scaleInRGB and sIsYUV:
        # Chroma upsampling
        if sIsSubS:
            if chromak_up == 'nnedi3':
                # Separate planes
                Y = core.std.ShufflePlanes(last, [0], vs.GRAY)
                U = core.std.ShufflePlanes(last, [1], vs.GRAY)
                V = core.std.ShufflePlanes(last, [2], vs.GRAY)
                # Chroma up-scaling
                U = nnedi3_resample_kernel(U, Y.width, Y.height, -sHCPlace / sHSubS, -sVCPlace / sVSubS, None, None, 1, nsize, nns, qual, etype, pscrn, opt, int16_prescreener, int16_predictor, exp, kernel, taps, a1, a2)
                V = nnedi3_resample_kernel(V, Y.width, Y.height, -sHCPlace / sHSubS, -sVCPlace / sVSubS, None, None, 1, nsize, nns, qual, etype, pscrn, opt, int16_prescreener, int16_predictor, exp, kernel, taps, a1, a2)
                # Merge planes
                last = core.std.ShufflePlanes([Y, U, V], [0, 0, 0], last.format.color_family)
            else:
                last = core.fmtc.resample(last, kernel=chromak_up, taps=chromak_up_taps, a1=chromak_up_a1, a2=chromak_up_a2, css="444", fulls=fulls, cplaces=cplaces)
        # Matrix conversion
        if mats == '2020cl':
            last = core.fmtc.matrix2020cl(last, fulls)
        else:
            last = core.fmtc.matrix(last, mat=mats, fulls=fulls, fulld=True, col_fam=vs.RGB, singleout=-1)
        fulls = True
    elif scaleInYUV and sIsRGB:
        # Matrix conversion
        if matd == '2020cl':
            last = core.fmtc.matrix2020cl(last, fulld)
        else:
            last = core.fmtc.matrix(last, mat=matd, fulls=fulls, fulld=fulld, col_fam=vs.YUV, singleout=-1)
        fulls = fulld
    
    # Scaling
    if scaleInGRAY or scaleInRGB:
        if gammaConv and sGammaConv:
            last = GammaToLinear(last, fulls, fulls, curves, sigmoid=sigmoid)
        elif sigmoid:
            last = SigmoidInverse(last)
        last = nnedi3_resample_kernel(last, target_width, target_height, src_left, src_top, src_width, src_height, scale_thr, nsize, nns, qual, etype, pscrn, opt, int16_prescreener, int16_predictor, exp, kernel, taps, a1, a2, invks, invkstaps)
        if gammaConv and dGammaConv:
            last = LinearToGamma(last, fulls, fulls, curved, sigmoid=sigmoid)
        elif sigmoid:
            last = SigmoidDirect(last)
    elif scaleInYUV:
        # Separate planes
        Y = core.std.ShufflePlanes(last, [0], vs.GRAY)
        U = core.std.ShufflePlanes(last, [1], vs.GRAY)
        V = core.std.ShufflePlanes(last, [2], vs.GRAY)
        # Scale Y
        Y = nnedi3_resample_kernel(Y, target_width, target_height, src_left, src_top, src_width, src_height, scale_thr, nsize, nns, qual, etype, pscrn, opt, int16_prescreener, int16_predictor, exp, kernel, taps, a1, a2)
        # Scale UV
        dCw = target_width // dHSubS
        dCh = target_height // dVSubS
        dCsx = ((src_left - sHCPlace) * hScale + dHCPlace) / hScale / sHSubS
        dCsy = ((src_top - sVCPlace) * vScale + dVCPlace) / vScale / sVSubS
        dCsw = src_width / sHSubS
        dCsh = src_height / sVSubS
        U = nnedi3_resample_kernel(U, dCw, dCh, dCsx, dCsy, dCsw, dCsh, scale_thr, nsize, nns, qual, etype, pscrn, opt, int16_prescreener, int16_predictor, exp, kernel, taps, a1, a2)
        V = nnedi3_resample_kernel(V, dCw, dCh, dCsx, dCsy, dCsw, dCsh, scale_thr, nsize, nns, qual, etype, pscrn, opt, int16_prescreener, int16_predictor, exp, kernel, taps, a1, a2)
        # Merge planes
        last = core.std.ShufflePlanes([Y, U, V], [0, 0, 0], last.format.color_family)
    
    # Color space conversion after scaling
    if scaleInGRAY and dIsYUV:
        dCw = target_width // dHSubS
        dCh = target_height // dVSubS
        last = Depth(last, depth=dbitPS, fulls=fulls, fulld=fulld)
        blkUV = core.std.BlankClip(last, dCw, dCh, color=[1 << (dbitPS - 1)])
        last = core.std.ShufflePlanes([last, blkUV, blkUV], [0, 0, 0], dColorFamily)
    elif scaleInGRAY and dIsRGB:
        last = Depth(last, depth=dbitPS, fulls=fulls, fulld=fulld)
        last = core.std.ShufflePlanes([last, last, last], [0, 0, 0], dColorFamily)
    elif scaleInRGB and dIsYUV:
        # Matrix conversion
        if matd == '2020cl':
            last = core.fmtc.matrix2020cl(last, fulld)
        else:
            last = core.fmtc.matrix(last, mat=matd, fulls=fulls, fulld=fulld, col_fam=dColorFamily, singleout=-1)
        # Chroma subsampling
        if dIsSubS:
            dCSS = '411' if dHSubS == 4 else '420' if dVSubS == 2 else '422'
            last = core.fmtc.resample(last, kernel=chromak_down, taps=chromak_down_taps, a1=chromak_down_a1, a2=chromak_down_a2, css=dCSS, fulls=fulld, cplaced=cplaced, invks=chromak_down_invks, invkstaps=chromak_down_invkstaps, planes=[2,3,3])
        last = Depth(last, depth=dbitPS, fulls=fulld)
    elif scaleInYUV and dIsRGB:
        # Matrix conversion
        if mats == '2020cl':
            last = core.fmtc.matrix2020cl(last, fulls)
        else:
            last = core.fmtc.matrix(last, mat=mats, fulls=fulls, fulld=True, col_fam=vs.RGB, singleout=-1)
        last = Depth(last, depth=dbitPS, fulls=True, fulld=fulld)
    else:
        last = Depth(last, depth=dbitPS, fulls=fulls, fulld=fulld)
    
    # Output
    return last


def nnedi3_resample_kernel(input, target_width=None, target_height=None, src_left=None, src_top=None, src_width=None, src_height=None, scale_thr=None, nsize=None, nns=None, qual=None, etype=None, pscrn=None, opt=None, int16_prescreener=None, int16_predictor=None, exp=None, kernel=None, taps=None, a1=None, a2=None, invks=False, invkstaps=3):
    core = vs.core
    
    # Parameters of scaling
    if target_width is None:
        target_width = input.width
    if target_height is None:
        target_height = input.height
    if src_left is None:
        src_left = 0
    if src_top is None:
        src_top = 0
    if src_width is None:
        src_width = input.width
    elif src_width <= 0:
        src_width = input.width - src_left + src_width
    if src_height is None:
        src_height = input.height
    elif src_height <= 0:
        src_height = input.height - src_top + src_height
    if scale_thr is None:
        scale_thr = 1.125
    
    src_right = src_width - input.width + src_left
    src_bottom = src_height - input.height + src_top
    
    hScale = target_width / src_width
    vScale = target_height / src_height
    
    # Parameters of nnedi3
    if nsize is None:
        nsize = 0
    if nns is None:
        nns = 3
    if qual is None:
        qual = 2
    
    # Parameters of fmtc.resample
    if kernel is None:
        kernel = 'spline36'
    else:
        kernel = kernel.lower()
    
    # Procedure decision
    hIsScale = hScale != 1
    vIsScale = vScale != 1
    isScale = hIsScale or vIsScale
    hResample = hIsScale or int(src_left) != src_left or int(src_right) != src_right
    vResample = vIsScale or int(src_top) != src_top or int(src_bottom) != src_bottom
    resample = hResample or vResample
    
    # Scaling
    last = input
    
    if hResample:
        last = core.std.Transpose(last)
        last = nnedi3_resample_kernel_vertical(last, target_width, src_left, src_width, scale_thr, nsize, nns, qual, etype, pscrn, opt, int16_prescreener, int16_predictor, exp, kernel, taps, a1, a2, invks, invkstaps)
        last = core.std.Transpose(last)
    if vResample:
        last = nnedi3_resample_kernel_vertical(last, target_height, src_top, src_height, scale_thr, nsize, nns, qual, etype, pscrn, opt, int16_prescreener, int16_predictor, exp, kernel, taps, a1, a2, invks, invkstaps)
    
    # Output
    return last


def nnedi3_resample_kernel_vertical(input, target_height=None, src_top=None, src_height=None, scale_thr=None, nsize=None, nns=None, qual=None, etype=None, pscrn=None, opt=None, int16_prescreener=None, int16_predictor=None, exp=None, kernel=None, taps=None, a1=None, a2=None, invks=False, invkstaps=3):
    core = vs.core
    
    # Parameters of scaling
    if target_height is None:
        target_height = input.height
    if src_top is None:
        src_top = 0
    if src_height is None:
        src_height = input.height
    elif src_height <= 0:
        src_height = input.height - src_top + src_height
    if scale_thr is None:
        scale_thr = 1.125
    
    scale = target_height / src_height # Total scaling ratio
    eTimes = math.ceil(math.log(scale / scale_thr, 2)) if scale > scale_thr else 0 # Iterative times of nnedi3
    eScale = 1 << eTimes # Scaling ratio of nnedi3
    pScale = scale / eScale # Scaling ratio of fmtc.resample
    
    # Parameters of nnedi3
    if nsize is None:
        nsize = 0
    if nns is None:
        nns = 3
    if qual is None:
        qual = 2
    
    # Parameters of fmtc.resample
    if kernel is None:
        kernel = 'spline36'
    else:
        kernel = kernel.lower()
    
    # Skip scaling if not needed
    if scale == 1 and src_top == 0 and src_height == input.height:
        return input
    
    # Scaling with nnedi3
    last = nnedi3_rpow2_vertical(input, eTimes, 1, nsize, nns, qual, etype, pscrn, opt, int16_prescreener, int16_predictor, exp)
    
    # Center shift calculation
    vShift = 0.5 if eTimes >= 1 else 0
    
    # Scaling with fmtc.resample as well as correct center shift
    w = last.width
    h = target_height
    sx = 0
    sy = src_top * eScale - vShift
    sw = last.width
    sh = src_height * eScale
    
    if h != last.height or sy != 0 or sh != last.height:
        if h < last.height and invks is True:
            last = core.fmtc.resample(last, w, h, sx, sy, sw, sh, kernel=kernel, taps=taps, a1=a1, a2=a2, invks=True, invkstaps=invkstaps)
        else:
            last = core.fmtc.resample(last, w, h, sx, sy, sw, sh, kernel=kernel, taps=taps, a1=a1, a2=a2)
    
    # Output
    return last


def nnedi3_rpow2_vertical(input, eTimes=1, field=1, nsize=None, nns=None, qual=None, etype=None, pscrn=None, opt=None, int16_prescreener=None, int16_predictor=None, exp=None):
    core = vs.core
    
    if eTimes >= 1:
        last = nnedi3_dh(input, field, nsize, nns, qual, etype, pscrn, opt, int16_prescreener, int16_predictor, exp)
        eTimes = eTimes - 1
        field = 0
    else:
        last = input
    
    if eTimes >= 1:
        return nnedi3_rpow2_vertical(last, eTimes, field, nsize, nns, qual, etype, pscrn, opt, int16_prescreener, int16_predictor, exp)
    else:
        return last


def nnedi3_dh(input, field=1, nsize=None, nns=None, qual=None, etype=None, pscrn=None, opt=None, int16_prescreener=None, int16_predictor=None, exp=None):
    core = vs.core
    return core.nnedi3.nnedi3(input, field=field, dh=True, nsize=nsize, nns=nns, qual=qual, etype=etype, pscrn=pscrn, opt=opt, int16_prescreener=int16_prescreener, int16_predictor=int16_predictor, exp=exp)


## Gamma conversion functions from HAvsFunc-r18
# Convert the luma channel to linear light
def GammaToLinear(src, fulls=True, fulld=True, curve='709', planes=[0, 1, 2], gcor=1., sigmoid=False, thr=0.5, cont=6.5):
    if not isinstance(src, vs.VideoNode) or src.format.bits_per_sample != 16:
        raise ValueError('GammaToLinear: This is not a 16-bit clip')
    
    return LinearAndGamma(src, False, fulls, fulld, curve.lower(), planes, gcor, sigmoid, thr, cont)

# Convert back a clip to gamma-corrected luma
def LinearToGamma(src, fulls=True, fulld=True, curve='709', planes=[0, 1, 2], gcor=1., sigmoid=False, thr=0.5, cont=6.5):
    if not isinstance(src, vs.VideoNode) or src.format.bits_per_sample != 16:
        raise ValueError('LinearToGamma: This is not a 16-bit clip')
    
    return LinearAndGamma(src, True, fulls, fulld, curve.lower(), planes, gcor, sigmoid, thr, cont)

def LinearAndGamma(src, l2g_flag, fulls, fulld, curve, planes, gcor, sigmoid, thr, cont):
    core = vs.core
    
    if curve == 'srgb':
        c_num = 0
    elif curve in ['709', '601', '170']:
        c_num = 1
    elif curve == '240':
        c_num = 2
    elif curve == '2020':
        c_num = 3
    else:
        raise ValueError('LinearAndGamma: wrong curve value')
    
    if src.format.color_family == vs.GRAY:
        planes = [0]
    
    #                 BT-709/601
    #        sRGB     SMPTE 170M   SMPTE 240M   BT-2020
    k0    = [0.04045, 0.081,       0.0912,      0.08145][c_num]
    phi   = [12.92,   4.5,         4.0,         4.5][c_num]
    alpha = [0.055,   0.099,       0.1115,      0.0993][c_num]
    gamma = [2.4,     2.22222,     2.22222,     2.22222][c_num]
    
    def g2l(x):
        expr = x / 65536 if fulls else (x - 4096) / 56064
        if expr <= k0:
            expr /= phi
        else:
            expr = ((expr + alpha) / (1 + alpha)) ** gamma
        if gcor != 1 and expr >= 0:
            expr **= gcor
        if sigmoid:
            x0 = 1 / (1 + math.exp(cont * thr))
            x1 = 1 / (1 + math.exp(cont * (thr - 1)))
            expr = thr - math.log(max(1 / max(expr * (x1 - x0) + x0, 0.000001) - 1, 0.000001)) / cont
        if fulld:
            return min(max(round(expr * 65536), 0), 65535)
        else:
            return min(max(round(expr * 56064 + 4096), 0), 65535)
    
    # E' = (E <= k0 / phi)   ?   E * phi   :   (E ^ (1 / gamma)) * (alpha + 1) - alpha
    def l2g(x):
        expr = x / 65536 if fulls else (x - 4096) / 56064
        if sigmoid:
            x0 = 1 / (1 + math.exp(cont * thr))
            x1 = 1 / (1 + math.exp(cont * (thr - 1)))
            expr = (1 / (1 + math.exp(cont * (thr - expr))) - x0) / (x1 - x0)
        if gcor != 1 and expr >= 0:
            expr **= gcor
        if expr <= k0 / phi:
            expr *= phi
        else:
            expr = expr ** (1 / gamma) * (alpha + 1) - alpha
        if fulld:
            return min(max(round(expr * 65536), 0), 65535)
        else:
            return min(max(round(expr * 56064 + 4096), 0), 65535)
    
    return core.std.Lut(src, planes=planes, function=l2g if l2g_flag else g2l)

# Apply the inverse sigmoid curve to a clip in linear luminance
def SigmoidInverse(src, thr=0.5, cont=6.5, planes=[0, 1, 2]):
    core = vs.core
    
    if not isinstance(src, vs.VideoNode) or src.format.bits_per_sample != 16:
        raise ValueError('SigmoidInverse: This is not a 16-bit clip')
    
    if src.format.color_family == vs.GRAY:
        planes = [0]
    
    def get_lut(x):
        x0 = 1 / (1 + math.exp(cont * thr))
        x1 = 1 / (1 + math.exp(cont * (thr - 1)))
        return min(max(round((thr - math.log(max(1 / max(x / 65536 * (x1 - x0) + x0, 0.000001) - 1, 0.000001)) / cont) * 65536), 0), 65535)
    
    return core.std.Lut(src, planes=planes, function=get_lut)

# Convert back a clip to linear luminance
def SigmoidDirect(src, thr=0.5, cont=6.5, planes=[0, 1, 2]):
    core = vs.core
    
    if not isinstance(src, vs.VideoNode) or src.format.bits_per_sample != 16:
        raise ValueError('SigmoidDirect: This is not a 16-bit clip')
    
    if src.format.color_family == vs.GRAY:
        planes = [0]
    
    def get_lut(x):
        x0 = 1 / (1 + math.exp(cont * thr))
        x1 = 1 / (1 + math.exp(cont * (thr - 1)))
        return min(max(round(((1 / (1 + math.exp(cont * (thr - x / 65536))) - x0) / (x1 - x0)) * 65536), 0), 65535)
    
    return core.std.Lut(src, planes=planes, function=get_lut)
## Gamma conversion functions from HAvsFunc-r18