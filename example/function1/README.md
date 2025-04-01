# 1. Compile function1.c into an object file (or directly into a static library)

`gcc -c -fPIC -Dconst= example/function1/function1.c -o example/function1/function1.o`

- -fPIC is crucial for shared libraries

# 2. Create the static library from the object file

`ar rcs example/function1/libfunction1.a example/function1/function1.o`

# 3. Compile wrapper.c and link it with the static library to create a shared library

`gcc -shared -fPIC example/function1/wrapper1.c -o example/function1/wrapper1.so -Iexample/function1 -Lexample/function1 -lfunction1`

- -fPIC is crucial for shared libraries
- -L. specifies the directory to look for libraries (current directory)
- -lfunction1 links against libfunction1.a