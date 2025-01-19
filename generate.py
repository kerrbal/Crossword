import sys

from crossword import *

class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("crossword/assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        all_nodes = self.domains.keys()
        for node in all_nodes:
            length_of_node = node.length
            all_words = self.domains[node]
            for word in all_words.copy():
                if len(word) != length_of_node:
                    self.domains[node].remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """

        is_revised = False
        constraints = self.crossword.overlaps[(x, y)]
        domain_1 = self.domains[x]
        domain_2 = self.domains[y]
        
        for possible_value in domain_1.copy():
            is_satisfied = False
            for check in domain_2:
                if possible_value == check:
                    continue
                if possible_value[constraints[0]] != check[constraints[1]]:
                    continue
                #if it succeeds to come so far, we say possible value in domain 1
                #is arc-consistent with value x in domain2
                is_satisfied = True
                break

            if not is_satisfied:
                self.domains[x].remove(possible_value)
                is_revised = True
        return is_revised

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if not arcs:
            arcs = [(var, neighbor) for var in self.domains.keys() for neighbor in self.crossword.neighbors(var) if neighbor != var]
        while len(arcs) != 0:
            x, y = arcs.pop(0)
            if self.revise(x, y):
                if len(self.domains[x]) == 0:
                    return False
                for neighbor in self.crossword.neighbors(x):
                    if neighbor != y:
                        arcs.append((neighbor, x))
        return True

            

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        all_variables = self.domains.keys()
        for i in all_variables:
            if i in assignment.keys():
                continue
            return False
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        constraints = self.crossword.overlaps
        for var in assignment.keys():
            if assignment[var] in self.domains[var]:
                neighbors = [neighbor for neighbor in self.crossword.neighbors(var) if neighbor in assignment.keys()]
                for neighbor in neighbors:
                    the_constraint = constraints[(var, neighbor)]
                    if the_constraint is None:
                        continue
                    var_word = assignment[var]
                    neighbor_word = assignment[neighbor]
                    if var_word[the_constraint[0]] == neighbor_word[the_constraint[1]]:
                        continue
                    return False

            else:
                return False
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        if var in assignment:
            return False
        the_neighbors = self.crossword.neighbors(var)
        minimum_affect = []
        possible_values = self.domains[var]
        counts_dict = {}
        neighboring_values = [value for neighbor in the_neighbors for value in self.domains[neighbor]]
        for one_value in possible_values:
            count = neighboring_values.count(one_value)
            if count in counts_dict:
                counts_dict[count].append(one_value)
            else:
                counts_dict[count] = [one_value]

        sorted_counts = list(counts_dict.keys())
        sorted_counts.sort()
        for i in sorted_counts:
            minimum_affect += counts_dict[i]
        
        return minimum_affect




    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        candidates = []
        min_remaining_values = float("inf")
        for i in self.domains.keys():
            if i not in assignment:
                values = self.domains[i]
                if len(values) < min_remaining_values:
                    candidates.clear()
                    candidates.append(i)
                if len(values) == min_remaining_values:
                    candidates.append(i)
        
        if len(candidates) == 1:
            return candidates[0]
        highest_degree = -1
        highest_degree_vertex = None
        for i in candidates:
            neighbors = self.crossword.neighbors(i)
            if len(neighbors) > highest_degree:
                highest_degree_vertex = i
        return highest_degree_vertex



    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """

        if not self.consistent(assignment):
            return None

        if self.assignment_complete(assignment):
            return assignment


        possible_assignment = self.select_unassigned_variable(assignment)
        value_candidates = self.order_domain_values(possible_assignment, assignment)
        if not value_candidates:
            print("something is off.")
            return assignment
        for value in value_candidates:
            if value in assignment.values():
                continue
            assignment[possible_assignment] = value
            is_done = self.backtrack(assignment)
            if is_done is None:
                assignment.pop(possible_assignment)
                continue
            self.consistent(is_done)
            return is_done
        return None

def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        print(sys.argv)
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
