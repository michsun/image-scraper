import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-q','--query',help='query to search for on search engine',type=str,required=True)
    parser.add_argument('-g','--google_search',help='search query on google', action='store_true',required=False)
    parser.add_argument('-p','--pinterest_search',help='search query on pinterest', action='store_true', required=False)

    args = parser.parse_args()
    if args.query:
        print(True)
    print(args.google_search)
    print(args.pinterest_search)


if __name__ == "__main__":
    main()
