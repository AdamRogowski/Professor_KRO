import os
import subprocess


def denoise_and_convert(
    directory="C:\\Users\\jaro\\Desktop\\git-projects\\numbers_prompt\\audio",
):
    # Ensure the output directory exists
    output_dir = os.path.join(directory, "processed_audio")
    os.makedirs(output_dir, exist_ok=True)

    # Loop through all .m4a files in the directory
    for filename in os.listdir(directory):
        if filename.endswith(".m4a"):
            input_path = os.path.join(directory, filename)
            output_path = os.path.join(
                output_dir, f"{os.path.splitext(filename)[0]}.mp3"
            )

            print(f"Processing {filename}...")

            # Denoise and trim silence
            command = [
                "ffmpeg",
                "-i",
                input_path,
                "-af",
                "afftdn=nf=-25,silenceremove=start_periods=1:start_silence=0.5:start_threshold=-30dB:detection=peak",
                output_path,
            ]

            # Run the command
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print(f"Processed files are saved in: {output_dir}")


# Run the function
denoise_and_convert()
