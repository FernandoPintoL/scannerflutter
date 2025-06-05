"""
Test script to verify package versions and compatibility with inference package requirements.

This script checks if the installed versions of packages meet the requirements
of the inference package, which needs:
- numpy 2.0.0-2.3.0
- opencv-python 4.8.1.78-4.10.0.84
- pillow 11.0-12.0
- supervision 0.25.1-0.30.0
"""
import pkg_resources
import sys

# Define the requirements of the inference package
INFERENCE_REQUIREMENTS = {
    'numpy': ('>=2.0.0', '<2.3.0'),
    'opencv-python': ('>=4.8.1.78', '<=4.10.0.84'),
    'pillow': ('>=11.0', '<12.0'),
    'supervision': ('>=0.25.1', '<=0.30.0')
}

def check_version(package_name, min_version=None, max_version=None):
    """
    Check if the installed version of a package meets the requirements.
    
    Args:
        package_name (str): Name of the package to check
        min_version (str): Minimum version required (inclusive)
        max_version (str): Maximum version allowed (inclusive)
        
    Returns:
        tuple: (is_installed, meets_requirements, installed_version)
    """
    try:
        # Get the installed version
        installed_version = pkg_resources.get_distribution(package_name).version
        is_installed = True
        
        # Check if the version meets the requirements
        meets_min = True if min_version is None else pkg_resources.parse_version(installed_version) >= pkg_resources.parse_version(min_version.lstrip('>='))
        meets_max = True if max_version is None else pkg_resources.parse_version(installed_version) <= pkg_resources.parse_version(max_version.lstrip('<='))
        
        meets_requirements = meets_min and meets_max
        
        return (is_installed, meets_requirements, installed_version)
    except pkg_resources.DistributionNotFound:
        return (False, False, None)

def main():
    print("Checking package versions for compatibility with inference package requirements...\n")
    
    all_requirements_met = True
    
    for package, (min_version, max_version) in INFERENCE_REQUIREMENTS.items():
        is_installed, meets_requirements, installed_version = check_version(package, min_version, max_version)
        
        if is_installed:
            status = "✓ COMPATIBLE" if meets_requirements else "✗ INCOMPATIBLE"
            print(f"{package}: {installed_version} {status}")
            print(f"  Required: {min_version} and {max_version}")
            
            if not meets_requirements:
                all_requirements_met = False
                if min_version and pkg_resources.parse_version(installed_version) < pkg_resources.parse_version(min_version.lstrip('>=')):
                    print(f"  Problem: Version too old. Please upgrade to at least {min_version.lstrip('>=')}.")
                elif max_version and pkg_resources.parse_version(installed_version) > pkg_resources.parse_version(max_version.lstrip('<=')):
                    print(f"  Problem: Version too new. Please downgrade to at most {max_version.lstrip('<=')}.")
        else:
            print(f"{package}: Not installed ✗")
            print(f"  Required: {min_version} and {max_version}")
            all_requirements_met = False
        
        print()
    
    if all_requirements_met:
        print("\nAll package versions are compatible with inference package requirements! ✓")
        return 0
    else:
        print("\nSome package versions are incompatible with inference package requirements. ✗")
        print("Please update the packages to the required versions.")
        return 1

if __name__ == "__main__":
    sys.exit(main())