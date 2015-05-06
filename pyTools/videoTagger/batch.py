__author__ = 'peter'
import os
import shutil
import pyTools.videoTagger.prepareFolderForVideoProcessing as PFFVP
import yaml

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
    for root, dirs, filenames in os.walk(sourceFolder):
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

    yamlString = yaml.dump(sorted(projects), default_flow_style=False)
    with open(project_cfg_path, 'w') as f:
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

