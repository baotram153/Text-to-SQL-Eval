import sys
import logging
import os


class Visualizer:
    '''
    - Contain logging methods
    - Evaluate exact matching, execution matching, and component matching
    - Instantiate only once for each benchmark run
    '''
    def __init__(self, root_dir=None, evaluation_file=None, logging_file=None):
        # prepare paths
        self.root_dir = root_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
        self.evaluation_file = evaluation_file or 'evaluation_results.txt'
        self.logging_file = logging_file or 'logging.txt'
        self.evaluation_path = os.path.join(self.root_dir, self.evaluation_file)
        self.logging_path = os.path.join(self.root_dir, self.logging_file)
        self._prepare_logging_file()

    def _prepare_logging_file(self):
        for path in [self.evaluation_path, self.logging_path]:
            if os.path.exists(path):
                logging.info(f'File {path} already exists, removing it.')
                os.remove(path)
            logging.info(f'Creating new file at {path}')
            os.makedirs(os.path.dirname(path), exist_ok=True)

    def write_scores_to_file(self, scores, etype, filename=None):
        filepath = os.path.join(self.root_dir,filename) if filename else self.evaluation_path
        logging.info(f'Writing scores to {filepath}')
        print(f'Writing scores to {scores} {etype}')
        # with open(filepath, 'a+') as f:
        #     self._write_scores(scores, etype, out=f)

    def write_scores_to_terminal(self, scores, etype):
        logging.info('Writing scores to terminal')
        self._write_scores(scores, etype, out=sys.stdout)

    def _write_scores(self, scores, etype, out=None):
        '''Print scores to terminal or a file.
        '''
        out = out or sys.stdout

        levels = ['easy', 'medium', 'hard', 'extra', 'all']
        partial_types = ['select', 'select(no AGG)', 'where', 'where(no OP)', 'group(no Having)',
                        'group', 'order', 'and/or', 'IUEN', 'keywords']

        print("{:20} {:20} {:20} {:20} {:20} {:20}".format("", *levels), file=out)
        counts = [scores[level]['count'] for level in levels]
        print("{:20} {:<20d} {:<20d} {:<20d} {:<20d} {:<20d}".format("count", *counts), file=out)

        if etype in ["all", "exec"]:
            print('=====================   EXECUTION ACCURACY     =====================', file=out)
            this_scores = [scores[level]['exec'] for level in levels]
            print("{:20} {:<20.3f} {:<20.3f} {:<20.3f} {:<20.3f} {:<20.3f}".format("execution", *this_scores), file=out)

        if etype in ["all", "match"]:
            print('\n====================== EXACT MATCHING ACCURACY =====================', file=out)
            exact_scores = [scores[level]['exact'] for level in levels]
            print("{:20} {:<20.3f} {:<20.3f} {:<20.3f} {:<20.3f} {:<20.3f}".format("exact match", *exact_scores), file=out)
            print('\n---------------------PARTIAL MATCHING ACCURACY----------------------', file=out)
            for type_ in partial_types:
                this_scores = [scores[level]['partial'][type_]['acc'] for level in levels]
                print("{:20} {:<20.3f} {:<20.3f} {:<20.3f} {:<20.3f} {:<20.3f}".format(type_, *this_scores), file=out)

            print('---------------------- PARTIAL MATCHING RECALL ----------------------', file=out)
            for type_ in partial_types:
                this_scores = [scores[level]['partial'][type_]['rec'] for level in levels]
                print("{:20} {:<20.3f} {:<20.3f} {:<20.3f} {:<20.3f} {:<20.3f}".format(type_, *this_scores), file=out)

            print('---------------------- PARTIAL MATCHING F1 --------------------------', file=out)
            for type_ in partial_types:
                this_scores = [scores[level]['partial'][type_]['f1'] for level in levels]
                print("{:20} {:<20.3f} {:<20.3f} {:<20.3f} {:<20.3f} {:<20.3f}".format(type_, *this_scores), file=out)

    def print_to_file(self, type, gold, pred, filename=None):
        '''
        :params type: str, type of comparison content (e.g., 'SQL String', 'SQL Dict', 'Table')
        '''
        filepath = os.path.join(self.root_dir, filename) if filename else self.logging_path
        logging.info(f'Writing evaluation results to {filepath}')
        with open(filepath, 'a') as f:
            f.write(f'Gold {type}: {gold}\n')
            f.write(f'Predicted {type}: {pred}\n')

    def print_end(self, filename=None):
        filepath = os.path.join(self.root_dir, filename) if filename else self.logging_path
        with open(filepath, 'a') as f:
            f.write('='*40 + '\n')