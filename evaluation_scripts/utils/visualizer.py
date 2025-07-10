class Visualizer:
    def __init__(self, etype, scores):
        self.scores = scores
        self.etype = etype

    def print_scores(self):
        levels = ['easy', 'medium', 'hard', 'extra', 'all']
        partial_types = ['select', 'select(no AGG)', 'where', 'where(no OP)', 'group(no Having)',
                        'group', 'order', 'and/or', 'IUEN', 'keywords']

        print("{:20} {:20} {:20} {:20} {:20} {:20}".format("", *levels))
        counts = [self.scores[level]['count'] for level in levels]
        print("{:20} {:<20d} {:<20d} {:<20d} {:<20d} {:<20d}".format("count", *counts))

        if self.etype in ["all", "exec"]:
            print('=====================   EXECUTION ACCURACY     =====================')
            this_scores = [self.scores[level]['exec'] for level in levels]
            print("{:20} {:<20.3f} {:<20.3f} {:<20.3f} {:<20.3f} {:<20.3f}".format("execution", *this_scores))

        if self.etype in ["all", "match"]:
            print('\n====================== EXACT MATCHING ACCURACY =====================')
            exact_scores = [self.scores[level]['exact'] for level in levels]
            print("{:20} {:<20.3f} {:<20.3f} {:<20.3f} {:<20.3f} {:<20.3f}".format("exact match", *exact_scores))
            print('\n---------------------PARTIAL MATCHING ACCURACY----------------------')
            for type_ in partial_types:
                this_scores = [self.scores[level]['partial'][type_]['acc'] for level in levels]
                print("{:20} {:<20.3f} {:<20.3f} {:<20.3f} {:<20.3f} {:<20.3f}".format(type_, *this_scores))

            print('---------------------- PARTIAL MATCHING RECALL ----------------------')
            for type_ in partial_types:
                this_scores = [self.scores[level]['partial'][type_]['rec'] for level in levels]
                print("{:20} {:<20.3f} {:<20.3f} {:<20.3f} {:<20.3f} {:<20.3f}".format(type_, *this_scores))

            print('---------------------- PARTIAL MATCHING F1 --------------------------')
            for type_ in partial_types:
                this_scores = [self.scores[level]['partial'][type_]['f1'] for level in levels]
                print("{:20} {:<20.3f} {:<20.3f} {:<20.3f} {:<20.3f} {:<20.3f}".format(type_, *this_scores))