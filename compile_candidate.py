#!/usr/bin/env python3
import argparse
import subprocess
import os


def main():
    parser = argparse.ArgumentParser(description="Merge a candidate and a template to a candidate and compile it.")
    parser.add_argument("candidate", type=str, nargs=1, help="The candidate to use")
    parser.add_argument("-t", dest="template", metavar="template", type=str, required=True, help="The template to use")
    args = parser.parse_args()
    with open(args.template, "r") as f:
        template_raw = f.read()
    with open(args.candidate[0], "r") as f:
        candidate_raw = f.read()
    candidate_basename = args.candidate[0].split('/')[-1]
    with open(f"./exec/{candidate_basename}.c", "w") as f:
        f.write(template_raw.replace("%%CANDIDATE%%", candidate_raw))
    os._exit(subprocess.call(f"gcc ./exec/{candidate_basename}.c -static -o ./exec/{candidate_basename}".split()))





if __name__ == "__main__":
    main()
