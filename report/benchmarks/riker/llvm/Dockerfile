FROM hs

RUN apt-get update && apt-get install -y git \
    clang \
    cmake

WORKDIR /

RUN git clone https://github.com/llvm/llvm-project.git && \
    cd llvm-project && \
    git checkout d28af7c654d8db0b68c175db5ce212d74fb5e9bc && \
    rm -rf llvm-build && \
    mkdir llvm-build && \
    cd llvm-build && \
    cmake -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -DCMAKE_BUILD_TYPE=Release -DLLVM_TARGETS_TO_BUILD=X86 -DLLVM_ENABLE_BINDINGS=0 ../llvm

COPY llvm_build.sh /llvm/llvm-build/llvm_build.sh