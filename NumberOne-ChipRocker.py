import os
import subprocess
from tqdm import tqdm
from datetime import datetime
import time
from termcolor import colored

# Constants
DEFAULT_MAGIC_OFFSET = 1610612736

# Helper Functions
def convert_size_to_bytes(size_str, unit):
    multipliers = {
        'b': 1,
        'kb': 1024,
        'mb': 1024**2,
        'gb': 1024**3,
    }
    return int(float(size_str) * multipliers[unit])

def get_flash_id():
    result = subprocess.run(['sudo', 'rkflashtool', 'i'], capture_output=True, text=True)
    return result.stdout.strip()

def rkflashtool_controller():
    while True:
        print("\\nRKFlashTool Controller Menu:")
        options = [
            ("b", "Reboot device"),
            ("l", "Load DDR init (MASK ROM MODE)"),
            ("L", "Load USB loader (MASK ROM MODE)"),
            ("v", "Read chip version"),
            ("n", "Read NAND flash info"),
            ("i", "Read IDBlocks"),
            ("j", "Write IDBlocks"),
            ("m", "Read SDRAM"),
            ("M", "Write SDRAM"),
            ("B", "Exec SDRAM"),
            ("r", "Read flash partition"),
            ("w", "Write flash partition"),
            ("p", "Fetch parameters"),
            ("P", "Write parameters"),
            ("e", "Erase flash (fill with 0xff)")
        ]
        
        for i, (_, desc) in enumerate(options):
            print(f"{i + 1}. {desc}")
        
        print("X. Exit to main menu")
        
        choice = input("Select an option: ")
        
        if choice.lower() == 'x':
            break
        
        if choice.isdigit() and 0 < int(choice) <= len(options):
            cmd, desc = options[int(choice) - 1]
            if cmd in ["l", "L", "j", "M", "w", "P"]:
                file_path = input(f"Enter the file path for {desc}: ")
                subprocess.run(['sudo', 'rkflashtool', cmd, file_path])
            else:
                subprocess.run(['sudo', 'rkflashtool', cmd])

def main():
    os.system('clear')
    
    # Animated intro with color
    print(colored("Initializing Wizard", 'blue'))
    time.sleep(1)
    os.system('clear')

    # Logo and intro
    print(colored("Number one", 'green').ljust(100))
    print(colored("   _|_|_|  _|        _|            _|_|_|                        _|                            ", 'white'))
    print(colored(" _|        _|_|_|        _|_|_|    _|    _|    _|_|      _|_|_|  _|  _|      _|_|    _|  _|_|  ", 'white'))
    print(colored(" _|        _|    _|  _|  _|    _|  _|_|_|    _|    _|  _|        _|_|      _|_|_|_|  _|_|      ", 'white'))
    print(colored(" _|        _|    _|  _|  _|    _|  _|    _|  _|    _|  _|        _|  _|    _|        _|        ", 'white'))
    print(colored("   _|_|_|  _|    _|  _|  _|_|_|    _|    _|    _|_|      _|_|_|  _|    _|    _|_|_|  _|        ", 'white'))
    print(colored("                         _|                                                                    ", 'white'))
    print(colored("                         _|                                                                    ", 'white'))
    

    print(colored("🧙 The ChipRocker wizard is a universal RockChip interface system ", 'green'))
    print(colored("used for dumping, writing, and interacting with RKXXX devices.", 'blue'))
    print(colored("Ensure you're in LOADER mode for flash I/O operations. 🧙", 'yellow'))
    time.sleep(2)

    subprocess.run(['sudo', 'rkflashtool', 'n'])

    device_dump = input(colored("Do you wish to jump directly to the dumping module? (Y/n, default Y): ", 'magenta')).strip().lower() != 'n'

    if not device_dump:
        rkflashtool_controller()
    else:
        # Dumping procedure
        custom_offset = input("📏 What starting offset would you like to use? (default: 1610612736): ") or str(DEFAULT_MAGIC_OFFSET)
        MAGIC_OFFSET = int(custom_offset, 0)  # Allow for hexadecimal input
        
        unit = input("📏 What unit of size would you like to use? (b/kb/mb/gb, default: mb): ").strip().lower() or 'mb'
        size_str = input(f"🔢 How many {unit.upper()} would you like to pull from the device? (default: 8): ") or '8'
        num_bytes = convert_size_to_bytes(size_str, unit)
        
        folder_path = input("📂 Where would you like to dump the pulled data? (e.g., /path/to/folder/, default: .): ") or '.'
        
        # Ask for custom dump name
        default_name = f"chiprocker_dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{get_flash_id()}.bin"
        custom_name = input(f"📂 Would you like to provide a custom name for the dump? (default: {default_name}): ") or default_name
    
        # Calculate the number of iterations and chunk size (1MB)
        chunk_size_bytes = 1024 * 1024
        num_chunks = (num_bytes + chunk_size_bytes - 1) // chunk_size_bytes
    
        # Read data in chunks
        part_files = []
        for i in tqdm(range(num_chunks), desc="🔄 Reading data", unit="MB"):
            offset = MAGIC_OFFSET + (i * chunk_size_bytes)
            chunk_bytes = min(chunk_size_bytes, num_bytes - (i * chunk_size_bytes))
            part_file_path = os.path.join(folder_path, f"dump_part_{i}.bin")
            part_files.append(part_file_path)
            subprocess.run([f'sudo rkflashtool m {offset} {chunk_bytes} > {part_file_path}'], shell=True)
    
        # Concatenate all chunks into one file
        final_dump_path = os.path.join(folder_path, custom_name)
        os.system(f"cat {' '.join(part_files)} > {final_dump_path}")
    
        # Delete temporary part files
        for part_file in part_files:
            os.remove(part_file)
    
        print(f"✅ Successfully read data from SDRAM. Dump saved at: {final_dump_path}")
        print("Thank you for using ChipRocker!")
        exit(0)  # Gracefully exit the program


if __name__ == "__main__":
    main()
