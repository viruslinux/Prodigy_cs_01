def decrypted(sentence):
    translation=""
    for element in sentence:
        if element in "1":
            translation += "a"
        elif element in "2":
            translation += "b"
        elif element in "3":
            translation += "c"
        elif element in "4":
            translation += "d"
        elif element in "5":
            translation += "e"
        elif element in "6":
            translation += "f"
        elif element in "7":
            translation += "g"
        elif element in "8":
            translation += "h"
        elif element in "9":
            translation += "i"
        elif element in "!":
            translation += "j"
        elif element in "@":
            translation += "k"
        elif element in "#":
            translation += "l"
        elif element in "$":
            translation += "m"
        elif element in "%":
            translation += "n"
        elif element in "^":
            translation += "o"
        elif element in "&":
            translation += "p"
        elif element in "*":
            translation += "q"
        elif element in ":":
            translation += "r"
        elif element in ";":
            translation += "s"
        elif element in "<":
            translation += "t"
        elif element in ">":
            translation += "u"
        elif element in "/":
            translation += "v"
        elif element in "(":
            translation += "w"
        elif element in ")":
            translation += "x"
        elif element in "-":
            translation += "y"
        elif element in "?":
            translation += "z"
        else:
            translation += element
    return translation

print(decrypted("**%$2445"))