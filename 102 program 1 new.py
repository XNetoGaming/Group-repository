##############################################################################
# Program 1
# Ricardo Almeida
# Professor K
# This program takes scores from a students race and takes their best score
# to print out and then ranks the top 3 in order
##############################################################################
import csv

# Function to calculate the final score for a list of scores
def calculate_final_score(scores):
    scores.sort()  
    total = 0
    for i in range(1, len(scores) - 1):
        total += scores[i]
    return total / 8  

# Function to read scores from a CSV file and calculate final scores for each student
def read_scores(filename):
    results = []  
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            name = row[0] 
            scores = []
            for score in row[1:]:
                scores.append(float(score))  
            final_score = calculate_final_score(scores) 
            results.append((name, final_score)) 
    return results

# Function to rank the results based on final scores
def rank_results(results):
    sorted_results = []
    for i in range(len(results)):
        for j in range(i + 1, len(results)):
            if results[i][1] < results[j][1]:
                results[i], results[j] = results[j], results[i]  
    sorted_results = results  

    # Creating a rankings dictionary
    rankings = {}
    for name, score in sorted_results:
        if score not in rankings:
            rankings[score] = [name]  
        else:
            rankings[score].append(name)  
    return rankings

# Function to print the rankings
def print_rankings(rankings):
    places = ['First', 'Second', 'Third']  
    i = 0
    for score, names in rankings.items():
        if i < 3:  
            print(places[i], "place:", ', '.join(names), "with a score of", round(score, 4))
            i += 1

# Main program
filename = 'scores.csv'  
results = read_scores(filename)  

# Print the final scores for each student
for result in results:
    print(result[0], "earned", round(result[1], 4))

# Rank the results and print the rankings
rankings = rank_results(results)  
print_rankings(rankings)  
