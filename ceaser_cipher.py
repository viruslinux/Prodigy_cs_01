import time

def caesar_cipher(text, shift, mode="enc"):
    """Encrypt or decrypt text using Caesar Cipher"""
    result = ""

    for char in text:
        if char.isalpha():  # shift only letters
            base = ord('A') if char.isupper() else ord('a')
            if mode == "enc":
                result += chr((ord(char) - base + shift) % 26 + base)
            else:  # decrypt
                result += chr((ord(char) - base - shift) % 26 + base)
        else:
            result += char  # keep spaces/punctuation unchanged
    return result


def intro():
    print("\n" + "="*60)
    print("WELCOME TO THE CAESAR CIPHER PROGRAM".center(60))
    print("="*60 + "\n")
    time.sleep(1)
    print("This tool allows you to encrypt and decrypt text using")
    print("the classic Caesar Cipher technique.\n")
    time.sleep(1)


def main():
    intro()

    while True:
        print("\nChoose an option:")
        print("1. Encrypt a message")
        print("2. Decrypt a message")
        print("3. Exit")

        choice = input("\nEnter your choice (1/2/3): ")

        if choice == "1":
            text = input("\nEnter the message to encrypt: ")
            shift = int(input("Enter shift number (e.g., 3): "))
            encrypted = caesar_cipher(text, shift, mode="enc")
            print("\nYour encrypted message is:")
            print("="*60)
            print(encrypted.center(60))
            print("="*60)

        elif choice == "2":
            text = input("\nEnter the message to decrypt: ")
            shift = int(input("Enter the shift number used for encryption: "))
            decrypted = caesar_cipher(text, shift, mode="dec")
            print("\nYour decrypted message is:")
            print("="*60)
            print(decrypted.center(60))
            print("="*60)

        elif choice == "3":
            print("\nExiting program... Goodbye!\n")
            break

        else:
            print("\nInvalid choice! Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()