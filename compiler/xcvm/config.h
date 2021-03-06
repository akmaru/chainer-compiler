#pragma once

#include <memory>

namespace chainer_compiler {

class CompilerConfig;

namespace xcvm {

// If `diversed` is true, returns a config which is different from the
// default config for testing purpose.
std::unique_ptr<CompilerConfig> GetCompilerConfig(bool diversed = false);

}  // namespace xcvm
}  // namespace chainer_compiler
