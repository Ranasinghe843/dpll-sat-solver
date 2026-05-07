import os

def clean_cnf_files(folder_path):
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory.")
        return

    for filename in os.listdir(folder_path):
        if filename.endswith(".cnf"):
            file_path = os.path.join(folder_path, filename)
            
            with open(file_path, 'r') as f:
                # Read the entire content and strip trailing whitespace/newlines
                content = f.read().rstrip()
                lines = content.splitlines()

            if len(lines) >= 2:
                # Check the last two meaningful lines
                if lines[-2].strip() == '%' and lines[-1].strip() == '0':
                    # Join all lines except the last two back together
                    new_content = "\n".join(lines[:-2])
                    
                    with open(file_path, 'w') as f:
                        f.write(new_content + "\n") # Adds one clean newline at the end
                    print(f"Successfully cleaned: {filename}")
                else:
                    print(f"Skipped: {filename} (Pattern '%' and '0' not found at end)")
            else:
                print(f"Skipped: {filename} (File too short)")

clean_cnf_files('./cnf/uf100-430')