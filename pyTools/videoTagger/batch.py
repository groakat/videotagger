__author__ = 'peter'
import os
import shutil
import pyTools.videoTagger.prepareFolderForVideoProcessing as PFFVP
import yaml
from PySide import QtGui, QtCore

def getRelativeFolder(root, subfolder):
    """
    Returns the relative folder so that
    os.path.join(root, res) == subfolder
    :param root:
    :param subfolder: abs path to subfolder within root
    :return: res
    """

    if subfolder.startswith(root):
        if not root.endswith(('/', '\\')):
            root += '/'
        return subfolder[len(root):]
    else:
        raise ValueError("subfolder must start with root path")


def prepareVideoSeries(sourceFolder, destinationFolder):
    projects = []
    project_cfg_path = os.path.join(destinationFolder, 'projects.yaml')


    folderWalk = list(os.walk(sourceFolder))

    # progress = QtGui.QProgressDialog("Copying files...", "Abort Copy", 0,
    #                                  sum([len(f) for r, d, f in folderWalk]), QtGui.QApplication.activeWindow())
    #
    # progress.setWindowModality(QtCore.Qt.WindowModal)
    # progress.setValue(0)
    # QtGui.QApplication.processEvents()

    cnt = 0
    for root, dirs, filenames in folderWalk:
        rel_folder = getRelativeFolder(sourceFolder, root)
        for filename in filenames:
            if filename.endswith(('.avi', '.mp4', '.mpeg')):
                if len(filenames) > 1:
                    bn = os.path.basename(filename).split('.')[0]
                    tmp_dest = os.path.join(destinationFolder, rel_folder, bn)
                    projects += [os.path.join(rel_folder, bn)]
                else:
                    tmp_dest = os.path.join(destinationFolder, rel_folder)
                    projects += [rel_folder]

                tmp_project_cfg_path = ''.join(['../' for x in range(rel_folder.count('/') + 1)])
                tmp_project_cfg_path += 'projects.yaml'

                if not os.path.exists(tmp_dest):
                    os.makedirs(tmp_dest)

                shutil.copy(os.path.join(root, filename), tmp_dest)
                PFFVP.prepareFolder(tmp_dest, projectCFGPath=tmp_project_cfg_path)

                cnt += 1
            # progress.setValue(cnt)

    yamlString = yaml.dump(sorted(projects), default_flow_style=False)

    with open(project_cfg_path, 'w') as f:
        f.writelines(yamlString)


def copySettingsIntoProject(project_cfg_path, settings_file):
        stream = file(settings_file, 'r')
        cfg_template = yaml.load(stream)
        if 'Project' not in cfg_template:
            cfg_template['Project'] = {}

        cfg_template["Project"]['project_path'] = project_cfg_path

        stream = file(project_cfg_path, 'r')
        projects = yaml.load(stream)
        root_folder = os.path.dirname(project_cfg_path)
        config_file = 'videoTaggerConfig.yaml'

        for rel_folder in projects:
            filename = os.path.join(root_folder,
                                    rel_folder,
                                    config_file)
            stream = file(filename, 'r')
            current_cfg_file = yaml.load(stream)

            cfg_template['Video']['videoPath'] = current_cfg_file['Video']['videoPath']
            cfg_template['Video']['videoExtension'] = current_cfg_file['Video']['videoExtension']


            yamlString = yaml.dump(cfg_template, default_flow_style=False)
            with open(filename, 'w') as f:
                f.writelines(yamlString)


def main():
    import argparse
    import textwrap
    parser = argparse.ArgumentParser(\
    formatter_class=argparse.RawDescriptionHelpFormatter,\
    description=textwrap.dedent(\
    """
    Copies all videos from the source-folder to the destination folder,
    creating a new project for each video file.

    It keeps the videos under a common project-series, which means that
    all videos can be accessed from VideoTagger by pressing the 'next'
    and 'previous' buttons in the interface.
    """),
    epilog=textwrap.dedent(\
    """
    ============================================================================
    Written and tested by Peter Rennert in 2015 as part of his PhD project at
    University College London.

    You can contact the author via p.rennert@cs.ucl.ac.uk

    I did my best to avoid errors and bugs, but I cannot privide any reliability
    with respect to software or hardware or data (including fidelity and potential
    data-loss), nor any issues it may cause with your experimental setup.

    <Licence missing>
    """))

    parser.add_argument('-s', '--source-folder',
                help="path to source folder")
    parser.add_argument('-d', '--destination-folder',
                help="path to destination folder")


    args = parser.parse_args()
    prepareVideoSeries(args.source_folder, args.destination_folder)

if __name__ == "__main__":
    main()

