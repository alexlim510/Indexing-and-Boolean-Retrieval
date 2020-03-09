#!/usr/bin/python3
import re
import nltk
import sys
import getopt
import math
import pickle

def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")

#The SkipList class that contains the posting list and the skip list
class SkipList:
    def __init__(self):        
        self.height = 1
        self.skipList0 = []
        self.skipList1 = []
        self.length = 0

    def __iter__(self):
        for docID in self.skipList0:
            yield docID

    #Searches for a docID and returns the index
    def find(self, key):
        if not self.skipList0:
            return -1

        curIndex = 0
        skipPointer = self.skipList1[0]

        while skipPointer:
            if self.skipList0[skipPointer]<=key:
                curIndex = skipPointer
                skipPointer = self.skipList1[skipPointer]
            else:
                break
                
        startIndex = curIndex
        
        for value in self.skipList0[startIndex:]:
            if value == key:
                return curIndex
            elif value < key:
                curIndex+=1
            else:
                return -1
        '''
        for i in range(self.height, -1, -1):            
            while(curNode.next[i] and curNode.next[i].value <= key):                
                curNode = curNode.next[i]
        '''
        return -1
    
    #Runs everytime an insertion or deletion is made
    #Ensures that the skip pointers is evenly distributed
    def maintainSkipPointers(self):
        numOfSkipPointers = int(math.sqrt(self.length))
        currentNumOfSkipPointers = 0
        if numOfSkipPointers < 2:
            return
        
        curIndex = 0
        
        for index in self.skipList1:
            if curIndex % numOfSkipPointers == 0 and\
                    currentNumOfSkipPointers < numOfSkipPointers:

                newSkipPointer = curIndex + numOfSkipPointers
                
                if newSkipPointer > self.length-1:
                    self.skipList1[curIndex] = None
                    currentNumOfSkipPointers = numOfSkipPointers
                else:
                    self.skipList1[curIndex] = newSkipPointer
                    currentNumOfSkipPointers+= 1
                
            else:
                self.skipList1[curIndex] = None

            curIndex += 1                
        

    def insertElement(self, key):
        if not self.skipList0:
            self.skipList0.append(key)
            self.skipList1.append(None)
            self.length+=1
            self.maintainSkipPointers()
            return True

        if self.find(key) > -1:
            return False
        else:
            self.skipList0.append(key)
            self.skipList0.sort()
            self.length+=1
            self.skipList1.append(None)
            self.maintainSkipPointers()            
    
    def deleteElement(self, key):

        if not self.skipList0:
            return False

        if self.find(key) > -1:
            self.skipList0.remove(key)
            self.length-=1
            self.skipList1.pop()
            self.maintainSkipPointers()
        else:
            return False

#Executes the AND operation
def andMerge(l1,l2):
    cur1 = 0
    cur2 = 0
    len1 = l1.length
    len2 = l2.length
    result = SkipList()

    if len1 == 0:
        return l2
    elif len2 == 0:
        return l1

    #The intersection algorithm using skip pointers
    while cur1 < len1 and cur2 < len2:        

        if l1.skipList0[cur1] < l2.skipList0[cur2]:
            if l1.skipList1[cur1] and\
                   l1.skipList0[l1.skipList1[cur1]] <= l2.skipList0[cur2]:
                cur1 = l1.skipList1[cur1]
            else:
                cur1 += 1

        elif l1.skipList0[cur1] > l2.skipList0[cur2]:
            if l2.skipList1[cur2] and\
                   l2.skipList0[l2.skipList1[cur2]] <= l1.skipList0[cur1]:
                cur2 = l2.skipList1[cur2]
            else:
                cur2+=1

        elif l1.skipList0[cur1] == l2.skipList0[cur2]:
            result.insertElement(l1.skipList0[cur1])
            cur1 += 1
            cur2 += 1
        
    return result

#Executes the OR operation
def orMerge(l1,l2):
    cur1 = 0
    cur2 = 0
    len1 = l1.length    
    len2 = l2.length
    result = SkipList()

    if len1 == 0:
        return l2
    elif len2 == 0:
        return l1

    #Adds element to the result if found in either lists
    while cur1 < len1 and cur2 < len2:            
        if l1.skipList0[cur1] < l2.skipList0[cur2]:
            result.insertElement(l1.skipList0[cur1])
            cur1 += 1

        elif l1.skipList0[cur1] > l2.skipList0[cur2]:
            result.insertElement(l2.skipList0[cur2])
            cur2 += 1
            
        else:
            result.insertElement(l2.skipList0[cur2])
            cur1 += 1 
            cur2 += 1

    #Adds remaining elements to the result
    if cur1 < len1:
        while cur1 < len1:
            result.insertElement(l1.skipList0[cur1])
            cur1 += 1

    if cur2 < len2:
        while cur2 < len2:
            result.insertElement(l2.skipList0[cur2])
            cur2 += 1
        
    return result

#Executes the NOT operation
def notMerge(l1):
    cur1 = 0
    cur2 = 0
    len1 = l1.length
    
    #largePosting contains the docIDs of all entries
    with open(POSTINGS_FILE,'rb') as f:                    
        f.seek(dictionary[" "][1])
        largePosting = pickle.load(f)
        
    len2 = largePosting.length
    result = SkipList()

    if len1 == 0:
        return largePosting

    #Remove Elements in largePosting that are found in l1
    while cur1 < len1 and cur2 < len2:            
        if l1.skipList0[cur1] > largePosting.skipList0[cur2]:
            cur2 += 1
            
        else:
            largePosting.deleteElement(l1.skipList0[cur1])
            cur1 += 1
            cur2 += 1
            
    return largePosting

#Prepare and executes the AND and OR operations
def executeOperation(curExecutionVals,curExecutionOps):
    defOps = ["AND","OR"]
    andVals = []
    orVals = []
    curVal = None
    
    numOps = len(curExecutionOps)
    numOfValues = len(curExecutionVals)
    
    if 'AND' in curExecutionOps:
        startIndex = curExecutionOps.index('AND')
        hasAnd = True
    else:
        startIndex = numOps
        hasAnd = False
        curVal = curExecutionVals.pop()
   
    
    #Retrieve posting lists for AND operation and sort by size
    if hasAnd:
        for i in range(startIndex,numOfValues):
            if i == numOfValues-1:
                curVal = curExecutionVals.pop()
            else:
                andVals.append(curExecutionVals.pop())
            
        andVals.sort(key = lambda val: val.length, reverse = True)

        #Execute AND operation
        while andVals:
            curVal = andMerge(curVal,andVals.pop())

    #Execute OR for the remaining posting lists
    if 'OR' in curExecutionOps:
        for i in range(startIndex):
            curVal = orMerge(curVal,curExecutionVals[i])
    return curVal

def parse(expression):
    defOps = {"AND":1,"OR":0,"NOT":1}

    #Stores posting lists and operators for query
    ops = []
    tokens = []

    #Temporary value and operator lists for preceded operations
    curExecutionTokens = []
    curExecutionOps = []
    isPreceded = False

    global dictionary
    with open(DICTIONARY_FILE,'rb') as f:
            dictionary = pickle.load(f)
            
    valList = expression.split(" ")    
    
    for val in valList:

        #If token is bracket, append to operator list
        if val == "(":
            ops.append("(")

        #Bulletproofing against syntax: "(TOKEN"
        #Adds "(" to operator list and posting list to vals
        elif val[0] == "(":
            ops.append("(")            
            try:
                pointer = dictionary[val[1:]][1]
                with open(POSTINGS_FILE,'rb') as f:                    
                    f.seek(pointer)
                    tokens.append(pickle.load(f))
            except:
                print("Token not found...")
                tokens.append(SkipList())
                    
        #Adds operator to operator list
        elif val.upper() in defOps:

            #If operator is OR, execute all AND and OR operators currently in
            #the operator list
            while ops and\
                  ops[-1] != "(" and\
                  defOps[val.upper()] < defOps[ops[-1]]:
                
                isPreceded = True
                curExecutionOps.append(ops.pop())
                curExecutionTokens.append(vals.pop())
                
            if isPreceded:
                curExecutionTokens.append(vals.pop())

                #The result of the operations will be added to the val list
                vals.append(executeOperation(curExecutionTokens,curExecutionOps))

                isPreceded = False
                curExecutionTokens.clear()
                curExecutionOps.clear()

            #Adds the OR operator to the list
            ops.append(val.upper())
                
        elif ")" in val:

            #Bulletproofing against syntax: "TOKEN)"
            #Adds posting list to vals
            if val[-1]== ")" and len(val)>1:
                token = val[:-1]
                try:
                    pointer = dictionary[token][1]
                    with open(POSTINGS_FILE,'rb') as f:
                        f.seek(pointer)
                        tokens.append(pickle.load(f))
                except:
                    print("Token not found...")
                    tokens.append(SkipList())                            
                    
            #If latest operator is NOT, execute it with the obtained posting list
            if ops and ops[-1] == "NOT":
                ops.pop()
                postingList = tokens.pop()
                tokens.append(notMerge(postingList))                


            #Execute the query in parenthesis
            while ops[-1] != "(":
                curExecutionOps.append(ops.pop())
                curExecutionTokens.append(tokens.pop())

            curExecutionTokens.append(tokens.pop())
            tokens.append(executeOperation(curExecutionTokens,curExecutionOps))
            #Clear temporary value and operator lists
            curExecutionTokens.clear()
            curExecutionOps.clear()

            #Remove left parenthesis from operation list
            ops.pop()


        else:
            #Obtain token
            try:
                pointer = dictionary[val][1]
                with open(POSTINGS_FILE,'rb') as f:
                    f.seek(pointer)
                    token = pickle.load(f)
            except:
                print("Token not found...")
                token = SkipList()
            
            #If latest operator is NOT, execute it with the obtained posting list
            if ops and ops[-1] == "NOT":
                ops.pop()
                tokens.append(notMerge(token)) 
                
            #Else add posting list to tokens
            else:
                tokens.append(token)

    if len(tokens)>0 and len(ops)>0:
        return executeOperation(tokens,ops)
    
    else:
        return tokens[0]

    
def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print('running search on the queries...')
    # This is an empty method
    # Pls implement your code in below

    global DICTIONARY_FILE
    DICTIONARY_FILE = dict_file
    global POSTINGS_FILE
    POSTINGS_FILE = postings_file

    #Loads the queries
    with open(queries_file,'r') as f:
        data = f.readlines()

    #Run the search and obtain results
    results = []
    for query in data:
        query = query.replace('\n','')
        results.append(parse(query))

    #Save the results to the results file
    outputList = ""
    with open(results_file,'w') as f:
        for result in results:
            output = "\""
            if result.length > 0:
                for i in result:                
                    output += str(i) + " "
                output = output[:-1]+ '\"' + '\n'
            else:
                output = output + '\"\"' + "\n"
            outputList+=output
        f.write(outputList)
            
            

dictionary_file = postings_file = file_of_queries = output_file_of_results = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file  = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None :
    usage()
    sys.exit(2)

run_search(dictionary_file, postings_file, file_of_queries, file_of_output)
