import re

# Mapping letters to their corresponding numeric values
LETTER_VALUES = {
    'A': 10, 'B': 12, 'C': 13, 'D': 14, 'E': 15, 'F': 16, 'G': 17, 'H': 18, 'I': 19,
    'J': 20, 'K': 21, 'L': 23, 'M': 24, 'N': 25, 'O': 26, 'P': 27, 'Q': 28, 'R': 29,
    'S': 30, 'T': 31, 'U': 32, 'V': 34, 'W': 35, 'X': 36, 'Y': 37, 'Z': 38
}

def calculate_check_digit(container_number):
    """Calculate the ISO 6346 check digit for a given container number."""
    # Weights corresponding to each position
    weights = [2**i for i in range(10)]
    
    total = 0
    for i, char in enumerate(container_number[:10]):
        if char.isdigit():
            value = int(char)
        else:
            value = LETTER_VALUES.get(char, 0)
        total += value * weights[i]
    
    remainder = total % 11
    return remainder if remainder < 10 else 0

def is_valid_container_number(container_number):
    """Validate the container number against ISO 6346 standards."""
    # Regular expression to match the format: 4 letters, 6 digits, 1 digit (check digit)
    if not re.match(r'^[A-Z]{4}\d{7}$', container_number):
        return False
    
    # Calculate the expected check digit
    expected_check_digit = calculate_check_digit(container_number)
    
    # Actual check digit is the last digit of the container number
    actual_check_digit = int(container_number[-1])
    
    return expected_check_digit == actual_check_digit

# Example usage
container_numbers = [
    "ECLU7102609",
    "MAEU4726827",
    "MAEU4064593",
    "MAEU4093884",
    "MAEU4127710",
    "MAEU4128105",
    "MAEU4132194",
    "MAEU4140142",
    "MAEU4145843",
    "MAEU4166430",
    "MAEU4183817",
    "MAEU4193646",
    "SUDU4872417",
    "SJKU5402427",
    "SJKU5403070",
    "AMFU5008749",
    "MMAU1227800",
    "MNBU0205806",
    "MNBU0212554",
    "MNBU0318340",
    "MNBU3509103",
    "MNBU4242156",
    "MWCU6760752",
    "SUDU5170035",
    "SUDU6272957",
    "PONU2971973",
    "MNBU0532898",
    "MWCU6818957",
    "SUDU6062689",
    "MNBU0651963",
    "MNBU3417732",
    "MNBU4076137",
    "MNBU9161777",
    "MNBU9167179",
    "MNBU0457650",
    "MNBU3341529",
    "SUDU6022480",
    "MMAU1062300",
    "MSWU0066215",
    "SUDU6061717",
    "MNBU3141161",
    "MSWU1000130",
    "SUDU8111210",
    "MNBU3057364",
    "MNBU3292466",
    "MSWU9074823",
    "SUDU6193230",
    "MNBU3016895",
    "MSWU1021745",
    "SUDU9300522",
    "FSCU5717797",
    "MNBU9050027",
    "MNBU3708912",
    "MNBU4019076",
    "MNBU4131888",
    "SUDU6180660",
    "MNBU3757938",
    "MNBU3825293",
    "MSWU0038527",
    "MSWU9080390",
    "SUDU6192872",
    "MNBU0236999",
    "MNBU0562022",
    "MNBU3075732"
]
container_numbers = [
    "ABCD1234567",
    "EFGH8910111",
    "IJKL1213141",
    "MNOP1516171",
    "QRST1819201",
    "UVWX2122231",
    "YZAB2425261",
    "CDEF2728291",
    "GHIJ3031321",
    "KLMN3334351",
    "OPQR3637381",
    "STUV3940411",
    "WXYZ4243441",
    "BCDE4546471",
    "FGHI4849501",
    "JKLM5152531",
    "NOPQ5455561",
    "RSTU5758591",
    "VWXY6061621",
    "ZABC6364651",
    "DEFG6667681",
    "HIJK6970711",
    "LMNO7273741",
    "PQRS7576771",
    "TUVW7879801",
    "XYZA8182831",
    "BCDF8485861",
    "EFGH8788891",
    "IJKL9091921",
    "MNOP9394951",
    "QRST9697981",
    "UVWX9910021",
    "YZAB1031041",
    "CDEF1051061",
    "GHIJ1071081",
    "KLMN1091101",
    "OPQR1111121",
    "STUV1131141",
    "WXYZ1151161",
    "BCDE1171181",
    "FGHI1191201",
    "JKLM1211221",
    "NOPQ1231241",
    "RSTU1251261",
    "VWXY1271281",
    "ZABC1291301",
    "DEFG1311321",
    "HIJK1331341",
    "LMNO1351361",
    "PQRS1371381",
    "TUVW1391401",
    "XYZA1411421",
    "BCDF1431441",
    "EFGH1451461",
    "IJKL1471481",
    "MNOP1491501",
    "QRST1511521",
    "UVWX1531541",
    "YZAB1551561",
    "CDEF1571581",
    "GHIJ1591601",
    "KLMN1611621",
    "OPQR1631641",
    "STUV1651661"
]



for container_number in container_numbers:
    if is_valid_container_number(container_number):
        print(f"{container_number} is valid.")
    else:
        print(f"{container_number} is invalid.")
