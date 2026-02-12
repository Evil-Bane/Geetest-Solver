import os
import shutil
import sys
import ddddocr

def patch_ddddocr():
    """
    Patches ddddocr v1.6.0 installation to resolve folder/file conflicts 
    (core/ vs core.py and utils/ vs utils.py) commonly seen on Python 3.13.
    """
    try:
        # Locate ddddocr package directory
        package_dir = os.path.dirname(ddddocr.__file__)
        print(f"[*] Found ddddocr at: {package_dir}")
        
        conflicts = ['core', 'utils']
        patched_count = 0
        
        for name in conflicts:
            folder_path = os.path.join(package_dir, name)
            file_path = os.path.join(package_dir, f"{name}.py")
            
            # Check if both folder and file exist
            if os.path.isdir(folder_path) and os.path.isfile(file_path):
                backup_name = f"{name}_backup"
                backup_path = os.path.join(package_dir, backup_name)
                
                if os.path.exists(backup_path):
                    print(f"[-] Backup folder {backup_name} already exists. Skipping {name} patch.")
                else:
                    print(f"[*] Conflict detected for '{name}'. Renaming folder to '{backup_name}'...")
                    try:
                        os.rename(folder_path, backup_path)
                        print(f"[+] Successfully renamed {name} folder. Python will now use {name}.py")
                        patched_count += 1
                    except Exception as e:
                        print(f"[!] Failed to rename {name}: {e}")
            elif os.path.isfile(file_path):
                print(f"[-] No folder conflict for '{name}' (only .py file exists).")
            elif os.path.isdir(folder_path):
                print(f"[-] No file conflict for '{name}' (only folder exists).")
            else:
                 print(f"[-] {name} not found in package.")

        if patched_count > 0:
            print("[+] Patching complete! Please restart your application.")
        else:
            print("[-] No patches applied (already patched or no conflicts found).")

    except Exception as e:
        print(f"[!] Error patching ddddocr: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    patch_ddddocr()
