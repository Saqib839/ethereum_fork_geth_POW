import sys

def generate_extradata(addresses: list[str]) -> str:
    # normalize and validate
    clean = [a.lower().replace("0x", "") for a in addresses]
    for a in clean:
        if len(a) != 40:
            raise ValueError(f"Invalid address length: {a}")

    # Clique requires signers sorted ascending
    clean_sorted = sorted(clean)

    vanity = "00" * 32
    signers = "".join(clean_sorted)
    seal = "00" * 65
    return "0x" + vanity + signers + seal

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 gen_extradata.py <addr1> <addr2> ... <addrN>")
        sys.exit(1)

    result = generate_extradata(sys.argv[1:])
    expected_len = 64 + (40 * len(sys.argv[1:])) + 130
    print(f"\nSigners: {len(sys.argv[1:])}")
    print(f"Length (should be {expected_len}): {len(result) - 2}")
    print(f"\n{result}\n")

# example usage
# python3 gen_extradata.py 0xAddr1... 0xAddr2... ... 0xAddr20...