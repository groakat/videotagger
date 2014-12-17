import pyTools.system.plugins as P

class TestPlugin(P.TutorialPlugin):
    def getMeta(self):
        """
        Function that return meta data of plugin
        :return: MetaData object
        """
        meta = P.MetaData(name='TestPlugin',
                        description='Simple Plugin to show how to implement interfaces')
        return meta
