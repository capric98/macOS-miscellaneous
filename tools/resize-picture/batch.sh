#!/bin/bash
Width=2560
Height=1600

Real_ESRGAN_URL="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/realesrgan-ncnn-vulkan-20210901-macos.zip"

function script_requirements() {
    echo "Requirements: curl, unzip, ffmpeg"
}

function resize() {
    pwidth=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of default=nw=1:nk=1 "${3}")
    pheight=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of default=nw=1:nk=1 "${3}")
    if [[ "${pwidth}" -gt "${1}" ]] || [[ "${pheight}" -gt "${2}" ]]; then
        echo "Copy \"${3}\" to \"${4}\"."
        cp "${3}" "${4}"
    else
        echo "Upscale \"${3}\" and save it to \"${4}\"."
        "${5}" -m "realesrgan-ncnn-vulkan-macos/models" -n "realesrgan-x4plus-anime" -i "${3}" -o "${4}"
    fi
}

command -v curl 2>&1 1>/dev/null || {script_requirements}
command -v unzip 2>&1 1>/dev/null || {script_requirements}
command -v ffmpeg 2>&1 1>/dev/null || {script_requirements}

REBIN="realesrgan-ncnn-vulkan-macos/realesrgan-ncnn-vulkan"

if [[ ! -d "realesrgan-ncnn-vulkan-macos" ]]; then
    echo "Real ESRGAN not found, start downloading..."
    curl -L "${Real_ESRGAN_URL}" -o "realesrgan-ncnn-vulkan-macos.zip"
    unzip "realesrgan-ncnn-vulkan-macos.zip" -d "realesrgan-ncnn-vulkan-macos"
    rm -rf "realesrgan-ncnn-vulkan-macos.zip"
    chmod u+x "${REBIN}"
fi

if [[ -z "${1}" ]]; then
    echo "Usage: batch.sh {dir}/{filename}"
    exit 1
fi

if [[ ! -d "${1}" ]]; then
    resize "${Width}" "${Height}" "${1}" "${1}.tmp.png" "${REBIN}"
    echo "scale=${Width}:${Height}:force_original_aspect_ratio=increase:flags=lanczos,crop=${Width}:${Height}"
    ffmpeg -i "${1}.tmp.png" -vf "scale=${Width}:${Height}:force_original_aspect_ratio=increase:flags=lanczos,crop=${Width}:${Height}" "${1%.*}_fit.png"
    rm -rf "${1}.tmp.png"
else
    mkdir "${1}/tmp" "${1}/fit"

    "${REBIN}" -m "realesrgan-ncnn-vulkan-macos/models" -n "realesrgan-x4plus-anime" -i "${1}" -o "${1}/tmp"
    for entity in "${1}"/*
    do
        if [[ ! -d "${entity}" ]]; then
            fn=$(basename -- "${entity}")
            resize "${Width}" "${Height}" ${entity} "${1}/tmp/${fn%.*}.png"
            ffmpeg -i "${1}/tmp/${fn%.*}.png" -vf "scale=${Width}:${Height}:force_original_aspect_ratio=increase:flags=lanczos,crop=${Width}:${Height}" "${1}/fit/${fn%.*}.png"
        fi
    done
    rm -rf "${1}/tmp"
fi