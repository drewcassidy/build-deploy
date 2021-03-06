import os
import shutil
import logging

from ksp_deploy.helpers import ensure_path, clean_path
from ksp_deploy.dependencies import download_dependency

logger = logging.getLogger('packager.packaging')


def build_nodep_release(version_data, mod_data, build_path, deploy_path):
    """
    Builds the release zip with no included dependencies

    Inputs:
        version_data (dict): Contents of the .version file
        mod_name (str): name of the mod
        build_path (str): path into which to build
        deploy_path (str): path into which to place zips for deploy
    """
    deploy_zip_path = os.path.join(deploy_path,
        f"{mod_data['mod-name']}_Core_" + "{MAJOR}_{MINOR}_{PATCH}".format(**version_data["VERSION"]))
    shutil.make_archive(deploy_zip_path, 'zip', os.path.join(build_path))
    logger.info(f"Packaged {build_path}")

def build_full_release(version_data, mod_data, build_path, deploy_path):
    """
    Builds the release zip with a full set of required dependencies

    Inputs:
        version_data (dict): Contents of the .version file
        mod_name (str): name of the mod
        build_path (str): path into which to build
        deploy_path (str): path into which to place zips for deploy
    """
    deploy_zip_path = os.path.join(deploy_path,
        f"{mod_data['mod-name']}_" + "{MAJOR}_{MINOR}_{PATCH}".format(**version_data["VERSION"]))
    shutil.make_archive(deploy_zip_path, 'zip', os.path.join(build_path))
    logger.info(f"Packaged {build_path}")

def build_extras(version_data, build_path, deploy_path, extras_path, extras_list=[], build_packages=False):
    """
    Compiles and optionally builds packages for all Extras in the mod

    Inputs:
        version_data (dict): Contents of the .version file
        build_path (str): path into which to build
        deploy_path (str): path into which to place zips for deploy
        build_packages (bool): whether to create an individual zipfile for each package
    """
    dirs = next(os.walk(extras_path))[1]
    for name in dirs:
        if len(extras_list) > 0:
            if name in extras_list:
                build_extra(name, version_data, build_packages, extras_path,build_path, deploy_path)
        else:
            build_extra(name, version_data, build_packages, extras_path,build_path, deploy_path)

def build_extra(name, version_data, build_package, extras_path, build_path, deploy_path):
    """
    Compiles and optionally builds a single Extras package

    Inputs:
        name (str): name of the extra
        version_data (dict): Contents of the .version file
        build_package (bool): whether to create an individual zipfile for the package
        build_path (str): path into which to build
        deploy_path (str): path into which to place zips for deploy
    """
    extra_path = os.path.join(deploy_path, f"{name}" + "{MAJOR}_{MINOR}_{PATCH}".format(**version_data["VERSION"]))
    logger.info(f"Packaging Extra {name}")
    ensure_path(os.path.join(build_path,"Extras"))
    shutil.copytree(os.path.join(extras_path, name), os.path.join(build_path,"Extras", name))

    if build_package:
        logger.info(f"Packaging {name}")
        shutil.make_archive(extra_path, "zip", os.path.join(build_path, "Extras", name))
        logger.info(f"Packaged {extra_path}")

def collect_dependencies(mod_data, build_path, config):
    """
    Finds and downloads all the mod's dependencies

    Inputs:
        mod_data (dict): the mod data dictionary
        build_path (str): path into which to build
    """
    dep_data = mod_data.get("dependencies", {})
    clean_path(config.TEMP_PATH)
    for name, info in dep_data.items():
        download_dependency(name, info, config.TEMP_PATH, build_path, config)
    cleanup(mod_data["package"]["included-support"], build_path)

def cleanup(kept_files, build_path):
    """
    Cleans up the trailing files in the main directory for packaging by excluding all expect the
    specified items in the mod's .mod_data.yml
    Inputs:
        kept_files (list[str]): list of files to keep
        build_path (str): path into which to build
    """
    onlyfiles = [f for f in os.listdir(build_path) if os.path.isfile(os.path.join(build_path, f))]
    for f in onlyfiles:
        if f not in kept_files:
            os.remove(os.path.join(build_path,f))
