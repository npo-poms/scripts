#!/usr/bin/env python3
""" """
import sys
import poms

def usage():
    print(sys.argv[0] + " [-r] [-h] [-s] [-t <target>] <MID> <image file>")

def main():

    opt, args = poms.opts(usage = usage, minargs = 2)
    mid, image = args

    print(poms.add_image(mid, image))



if __name__ == "__main__":
    main()
