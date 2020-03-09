#!/usr/bin/python3
import re
import nltk
import sys
import getopt
import pickle
import os
import math
from pathlib import Path

stemmer = nltk.stem.porter.PorterStemmer()

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

#Return list of tokens from a file
def tokenizer(text):
    sentences = nltk.sent_tokenize(text)
    tokens = []
    for sentence in sentences:
        tokenized_sentence = nltk.word_tokenize(sentence)
        for word in tokenized_sentence:
            tokens.append(stemmer.stem(word))
    return tokens

#Return list of token and docID pairs from a file
def createTokenIDPairs(tokens,docID):    
    tokenIDPairs = []
    for token in tokens:
        tokenIDPairs.append((token,docID))
    return tokenIDPairs


def createDictionaryAndPostings(tokenIDPairs,sortedEntries,output_file_dictionary,output_file_postings):
    print("Creating dictionary and posting lists...")    

    curNumberOfTokens = 0
    curTokenIDPair = None

    #dictionary = {'TOKEN' : [FREQUENCY,POINTER]}
    #Initialise first token in dictionary
    dictionary = {}

    #postingList
    postingList = SkipList()
    
    curToken = None
    prevToken = None

    #Stores the current total size in the postings.txt file
    curSize = 0
    start = True
    
    for tokenIDPair in tokenIDPairs:
        
        #If token is new, add new token to dictionary and posting list
        if tokenIDPair[0] != curToken:        

            if not start:
                with open(output_file_postings,'ab') as f:
                    curSize += len(pickle.dumps(postingList))
                    pickle.dump(postingList,f)
            else:
                start = False
            
            #Initialise previous and current token
            prevToken = curToken
            curToken = tokenIDPair[0]
            

            #Update posting list and dictionary with new token
            curNumberOfTokens+=1
            dictionary[curToken]=[1,curSize]            
            postingList = SkipList()
            postingList.insertElement(tokenIDPair[1])
            

        #If token is already in dictionary
        else:
            
            #Increment frequency of token in dictionary
            dictionary[curToken][0]+=1
            
            #Inserts doc ID into posting list
            postingList.insertElement(tokenIDPair[1])
            
            
    
    #Save latest posting list
    with open(output_file_postings,'ab') as f:
        curSize += len(pickle.dumps(postingList))
        pickle.dump(postingList,f)
    
                
    
    #Add last posting list consisting of all files
    dictionary[" "] = [len(sortedEntries),curSize]
    postingList = SkipList()
    
    for i in sortedEntries:
        postingList.insertElement(i)
    
    with open(output_file_postings,'ab') as f:
        pickle.dump(postingList,f)

    #Save dictionary
    print("Saving dictionary...")
    with open(output_file_dictionary,"wb") as f:
        pickle.dump(dictionary, f)


def build_index(input_directory, output_file_dictionary, output_file_postings):
    directory = 'C:/Users/NTU/AppData/Roaming/nltk_data/corpora/reuters/training/'

    #Retrieves the list of files in the directory
    entries = os.listdir(input_directory)    
    unsortedEntries = list(map(lambda a : int(a), entries))
    unsortedEntries.sort()
    sortedEntries = list(map(lambda a : str(a), unsortedEntries))
    dataFolder = Path(directory)

    tokenIDPairs = []

    #Reads each reuter file and obtain tokens
    print("Creating TokenIDPairs...")
    for i in sortedEntries:
        file_to_open = dataFolder / i
        with open(file_to_open,'r') as f:
            text = f.read()
            tokens = tokenizer(text)
            tokenIDPairs.extend(createTokenIDPairs(tokens,int(i)))

    #Remove deplicate tokenID pairs
    tokenIDPairs = list(set(tokenIDPairs))
    
    tokenIDPairs.sort(key=lambda tup: tup[0])
    sortedEntries = list(map(lambda i: int(i),sortedEntries))
    createDictionaryAndPostings(tokenIDPairs,sortedEntries,output_file_dictionary,output_file_postings)

    
def usage():
    print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")


    

input_directory = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-i': # input directory
        input_directory = a
    elif o == '-d': # dictionary file
        output_file_dictionary = a
    elif o == '-p': # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"

if input_directory == None or output_file_postings == None or output_file_dictionary == None:
    usage()
    sys.exit(2)

build_index(input_directory, output_file_dictionary, output_file_postings)
