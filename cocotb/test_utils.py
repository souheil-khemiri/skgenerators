"""
This module contains test utilities for cocotb simulations.
"""
import numpy as np

class matrix:
    """Generate and iterate through random matrix square matrix."""
    def __init__(self, size, dtype ):
        """
        initialize a random matrix.

        Args :
            size: Dimension of a  square matrix (size x size )
            ELEMENT_TYPE: Type of the element 
            dtype: numpy data type  np.int8 — 8-bit signed integer
                                    np.int16 — 16-bit signed integer
                                    np.int32 — 32-bit signed integer
                                    np.int64 — 64-bit signed integer
        """
        low = np.iinfo(dtype).min
        high = np.iinfo(dtype).max 
        self.matrix=matrix = np.random.randint(  low, high, size=(size,size), dtype=dtype)
        self.__counter = 0
        self.size=size
        
    def get_next_top_row(self):
        """itirate over rows starting from the top"""
        if self.__counter < self.size:
            row = self.matrix[self.__counter, :]
            self.__counter += 1
            return row
        else:
            self.__counter = 0
            raise StopIteration("Reached end of matrix")

    def get_next_bottom_row(self):
        """itirate over rows starting from the bottom"""
        if self.__counter < self.size:
            row = self.matrix[self.size -1 - self.__counter, :]
            self.__counter +=1
            return row
        else:
            self.__counter = 0
            raise StopIteration("Reached end of matrix")
    def get_next_rightous_col(self):
        """itirate over columns starting from the right"""
        if self.__counter < self.size:
            row = self.matrix[:, self.size -1 - self.__counter]
            self.__counter +=1
            return row
        else:
            self.__counter = 0
            raise StopIteration("Reached end of matrix")

    def get_next_leftist_col(self):
        """itirate over columns starting from the left"""
        if self.__counter < self.size:
            row = self.matrix[:,self.__counter]
            self.__counter +=1
            return row
        else:
            self.__counter = 0
            raise StopIteration("Reached end of matrix")

    def reset(self):
        """Reset counter to 0"""
        self.__counter = 0







if __name__ == "__main__":
    m = marix(4, np.int8)
    
    print("\n" + "="*50)
    print("FULL MATRIX (4x4):")
    print("="*50)
    print(m.matrix)
    print(f"\nShape: {m.matrix.shape}, Dtype: {m.matrix.dtype}")
    
    print("\n" + "="*50)
    print("TESTING get_next_top_row():")
    print("="*50)
    
    m.reset()
    all_correct = True
    for i in range(m.size):
        row = m.get_next_top_row()
        original = m.matrix[i, :]
        matches = np.array_equal(row, original)
        status = "OK" if matches else "MISMATCH"
        print(f"Row {i}: {row} [{status}]")
        all_correct = all_correct and matches
    
    print(f"All rows correct: {all_correct}")
    
    print("\n" + "="*50)
    print("TESTING get_next_bottom_row():")
    print("="*50)
    
    m.reset()
    all_correct = True
    for i in range(m.size):
        row = m.get_next_bottom_row()
        expected = m.matrix[m.size - 1 - i, :]
        matches = np.array_equal(row, expected)
        status = "OK" if matches else "MISMATCH"
        print(f"Bottom Row {i}: {row} [{status}]")
        all_correct = all_correct and matches
    
    print(f"All bottom rows correct: {all_correct}")
    
    print("\n" + "="*50)
    print("TESTING get_next_leftist_col():")
    print("="*50)
    
    m.reset()
    all_correct = True
    for i in range(m.size):
        col = m.get_next_leftist_col()
        original = m.matrix[:, i]
        matches = np.array_equal(col, original)
        status = "OK" if matches else "MISMATCH"
        print(f"Left Col {i}: {col} [{status}]")
        all_correct = all_correct and matches
    
    print(f"All left columns correct: {all_correct}")
    
    print("\n" + "="*50)
    print("TESTING get_next_rightous_col():")
    print("="*50)
    
    m.reset()
    all_correct = True
    for i in range(m.size):
        col = m.get_next_rightous_col()
        expected = m.matrix[:, m.size - 1 - i]
        matches = np.array_equal(col, expected)
        status = "OK" if matches else "MISMATCH"
        print(f"Right Col {i}: {col} [{status}]")
        all_correct = all_correct and matches
    
    print(f"All right columns correct: {all_correct}")

