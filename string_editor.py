import struct
import sys
import os

WWEL0GO_BYTES = b'\xEE\x80\x98'
WWEL0GO_PLACEHOLDER = '*wwelogo*'

def read_strings(file_path):
    with open(file_path, 'rb') as f:
        header = f.read(4)
        if header != b'\x00\x00\x00\x00':
            print("Invalid file extension.")
            return
        toc_length = struct.unpack('I', f.read(4))[0]

        entries = []
        for _ in range(toc_length):
            offset, length, id, _ = struct.unpack('IIII', f.read(16))
            entries.append((offset, length, id))

        strings = {}
        for offset, length, id in entries:
            f.seek(offset)
            text_data = f.read(length - 1).decode('utf-8', errors='replace')  # -1 to exclude the text delimiter
            text_data = text_data.replace(WWEL0GO_BYTES.decode('utf-8', 'replace'), WWEL0GO_PLACEHOLDER)
            strings[id] = text_data

    with open(file_path.replace('.pac', '.txt'), 'w', encoding='utf-8') as f:
        for id, text in sorted(strings.items()):
            f.write(f'{id}: {text}\n')

        print("Text strings extracted successfully.")


def write_strings(file_path):
    new_file_path = input("Enter the path for the new file: ")
    with open(file_path, 'rb') as f_original:
        header = f_original.read(4)
        if header != b'\x00\x00\x00\x00':
            print("Invalid file extension.")
            return
        original_data = f_original.read()

    # Read strings from text file
    strings = {}
    current_id = None
    lines = []
    with open(file_path.replace('.pac', '.txt'), 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n').replace(WWEL0GO_PLACEHOLDER, WWEL0GO_BYTES.decode('utf-8', errors='replace'))
            if ': ' in line:
                if current_id is not None:
                    strings[current_id] = '\x0a'.join(lines)
                current_id, text = line.split(': ', 1)
                current_id = int(current_id)
                lines = [text]
            elif line == "":
                lines.append('')
            elif current_id is not None:
                lines.append(line)
            else:
                print(f"Skipping line: {line}")
    if current_id is not None:
        strings[current_id] = '\x0a'.join(lines)

    with open(file_path, 'rb') as f_original:
        original_data = f_original.read()
    
    toc_length, = struct.unpack('I', original_data[4:8])
    entries = [list(struct.unpack('IIII', original_data[8 + 16 * i:24 + 16 * i])) for i in range(toc_length)]
    
    new_data = bytearray(original_data)
    new_texts_end = len(new_data)
    
    for entry in entries:
        offset, length, id, _ = entry
        if id in strings:
            text = strings[id]
            if all(ord(char) < 128 or char == WWEL0GO_BYTES.decode('utf-8') for char in text):
                text_data = text.encode('utf-8') + b'\x00'
                new_length = len(text_data)
    
                if new_length <= length:
                    new_data[offset:offset + length] = text_data.ljust(length, b'\x00')
                else:
                    new_offset = new_texts_end
                    new_texts_end += new_length
                    new_data.extend(text_data)
                    entry[0] = new_offset  # Update offset in the entry
                    entry[1] = new_length  # Update length in the entry
            else:
                print(f"Skipping non-ASCII text (ID: {id}): {text}")
        else:
            print(f"Missing text for ID: {id}")
    
    # Update the table of contents
    for i, entry in enumerate(entries):
        new_data[8 + 16 * i : 24 + 16 * i] = struct.pack('IIII', *entry[:3], 0)
    
    # Write the updated data to the new file
    with open(new_file_path, 'wb') as f_new:
        f_new.write(new_data)
    
    print(f"File rebuilt successfully and saved to {new_file_path}")


def main():
    while True:
        print("Select an option:")
        print("1. Extract file")
        print("2. Rebuild file")
        print("3. Exit")
        choice = input("Enter the number of your choice: ")

        if choice == '1':
            file_path = input("Enter the path of the file: ")
            read_strings(file_path)
            
        elif choice == '2':
            file_path = input("Enter the path of the file: ")
            write_strings(file_path)
            
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 3.")

if __name__ == "__main__":
    main()
