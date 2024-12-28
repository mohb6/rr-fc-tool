from dataclasses import dataclass
from typing import Tuple, List, Optional
import hashlib, struct, random, zlib, sys
from pathlib import Path
from pystyle import Colors, Colorate, Center

def colorprint(text: str) -> None:
    print(Colorate.Horizontal(Colors.red_to_white, text))

def colorinput(prompt: str) -> str:
    return input(Colorate.Horizontal(Colors.red_to_white, prompt))

@dataclass
class FriendCode:
    pid: int
    code: str

class calc:
    GAME_ID, MAX_PID = "JCMR", 0xFFFFFFFF
    
    @staticmethod
    def calcfc(pid: int) -> str:
        if not (0 <= pid <= calc.MAX_PID): 
            raise ValueError(f"pid must be a 32-bit integer (0 to {calc.MAX_PID}).")
        data_block = struct.pack('<I', pid) + calc.GAME_ID.encode('utf-8')
        checksum_byte = (hashlib.md5(data_block).digest()[0] >> 1) & 0x7F
        friend_code = f"{((checksum_byte << 32) | pid):012d}"
        return f"{friend_code[:4]}-{friend_code[4:8]}-{friend_code[8:]}"

    @staticmethod
    def fc2pid(friend_code: str) -> int:
        if not (len(friend_code) == 14 and friend_code[4] == '-' and friend_code[9] == '-' and friend_code.replace("-", "").isdigit()): 
            raise ValueError("fc must be in format XXXX-YYYY-ZZZZ")
        return int(friend_code.replace("-", "")) & calc.MAX_PID

class files:
    @staticmethod
    def procrkp(file_path: Path) -> int:
        try:
            with open(file_path, 'r+b') as file:
                file.seek(0x40)
                raw_values = file.read(0x3C)
                little_endian_bytes = bytearray()
                [little_endian_bytes.extend(reversed(raw_values[i:i+4])) for i in range(0, len(raw_values), 4)]
                crc_value = zlib.crc32(little_endian_bytes) & 0xFFFFFFFF
                file.seek(0x7C)
                file.write(struct.pack('>I', crc_value))
                return crc_value
        except Exception as e: 
            colorprint(f"error processing file: {e}")
            return 0

    @staticmethod
    def fc2rkp(file_path: Path, decimal_value: int) -> bool:
        try:
            if not (0 <= decimal_value <= calc.MAX_PID): 
                raise ValueError("value must be a 32-bit unsigned integer")
            with open(file_path, 'r+b') as file:
                file.seek(0x5C)
                file.write(struct.pack('>I', decimal_value))
            return True
        except Exception as e: 
            colorprint(f"error writing to file: {e}")
            return False

class rr:
    @staticmethod
    def calc(limit: int = 300) -> List[FriendCode]:
        valid_codes = []
        while len(valid_codes) < limit:
            pid = random.randint(0, calc.MAX_PID)
            friend_code = calc.calcfc(pid)
            if len(set(friend_code.replace("-", ""))) == 4:
                valid_codes.append(FriendCode(pid, friend_code))
                if len(valid_codes) % 10 == 0:
                    colorprint(f"found {len(valid_codes)} fc")
        return valid_codes

def main():
    while True:
        menu = """
rewritten by mookie
1. pid2fc
2. fc2pid
3. genfc
4. process rkp
5. writefc2rkp
6. exit
"""
        colorprint(menu)
        choice = colorinput("enter choice: ")
        
        try:
            if choice == "1":
                pid = colorinput("enter pid: ")
                result = calc.calcfc(int(pid))
                colorprint(f"fc: {result}")
            elif choice == "2":
                fc = colorinput("enter fc (XXXX-YYYY-ZZZZ): ")
                result = calc.fc2pid(fc)
                colorprint(f"pid: {result}")
            elif choice == "3":
                amount = colorinput("enter fc amt (default 300): ") or "300"
                codes = rr.calc(int(amount))
                for code in codes:
                    colorprint(f"pid: {code.pid}, fc: {code.code}")
            elif choice == "4":
                path = colorinput("enter rkp file path: ")
                result = files.procrkp(Path(path))
                colorprint(f"CRC-32: {result:#08X}")
            elif choice == "5":
                path = colorinput("enter rkp file path: ")
                value = colorinput("enter value: ")
                if files.fc2rkp(Path(path), int(value)):
                    colorprint("wrote fc to rkp")
            elif choice == "6":
                sys.exit(0)
            else:
                colorprint("invalid choice")
                
        except ValueError as e:
            colorprint(f"error: {e}")

if __name__ == "__main__":
    main()