from buildbot.schedulers.basic import SingleBranchScheduler

class TwistedScheduler(SingleBranchScheduler):
    @staticmethod
    def fileIsImportant(change):
        for filename in change.files:
            if not filename.startswith("docs/fun/"):
                return 1
        return 0
