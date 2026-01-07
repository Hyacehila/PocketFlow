# PocketFlow的Class Abstract

我们需要使用四个需要单独导入的Python Package，他们都是用来实现一些必要的功能

```python
import asyncio, warnings, copy, time
```

分别用于实现异步，配套异步使用的时间系列函数，警告信息以及对象的复制。

## BaseNode

所有的Node和Flow的基础，我们在后面会介绍到，在PocketFlow的抽象结构中，Flow也是一种特殊的Node，从而实现Node和Flow的混合嵌套以及Flow对Flow的嵌套。

```python
class BaseNode:
    def __init__(self): self.params,self.successors={},{}
    def set_params(self,params): self.params=params
    def next(self,node,action="default"):
        if action in self.successors: warnings.warn(f"Overwriting successor for action '{action}'")
        self.successors[action]=node; return node
    def prep(self,shared): pass
    def exec(self,prep_res): pass
    def post(self,shared,prep_res,exec_res): pass
    def _exec(self,prep_res): return self.exec(prep_res)
    def _run(self,shared): p=self.prep(shared); e=self._exec(p); return self.post(shared,p,e)
    def run(self,shared): 
        if self.successors: warnings.warn("Node won't run successors. Use Flow.")  
        return self._run(shared)
    def __rshift__(self,other): return self.next(other)
    def __sub__(self,action):
        if isinstance(action,str): return _ConditionalTransition(self,action)
        raise TypeError("Action must be a string")
```

用于构造类的基本属性，我们引入构造函数，为所有的BaseNode以及后面的继承类一共两个基本属性，`params` 以及 `successors` 分别用于刻画结点的参数设置以及他的继任者。

```python
def __init__(self): self.params,self.successors={},{}
```

用于设置参数，我们需要引入对应的设置参数的方法，如下

```python
def set_params(self,params): self.params=params
```

为了构造结点之间的链接，我们需要定义对应的方法来设置结点的下一个结点，他接受动作及其对应的结点，修改 `successors` 参数，并且返回`node`自身用于为了实现链式调用。并且提供了重复设置的警告，防止因为以外覆盖以前完成的结点。

```python
def next(self,node,action="default"):
        if action in self.successors: warnings.warn(f"Overwriting successor for action '{action}'")
        self.successors[action]=node; return node
```

对于具体的结点逻辑，提供三个占位用的方法，具体他们是用来做什么的，由其子类来进行填充，这是在自行构建 `node` 的时候需要修改的核心。

```python
def prep(self,shared): pass
def exec(self,prep_res): pass
def post(self,shared,prep_res,exec_res): pass
```

关于结点的执行，设计了三个重要的方法。分别是 `_exec` , `_run` ,`run` ；`_exec` 只负责调用 `exec` 函数，之所以需要设计这个内部方法是为了在后面的子类中方便自由的重写执行时的逻辑，而避免修改应该由开发者设计的`exec` 函数，从而实现清晰的抽象。 `_run` 实现了内部的执行逻辑。`run` 则是用于启动执行逻辑，但是也为执行单个结点预留了空间，并正确的给出了警告信息。

```python
def _exec(self,prep_res): return self.exec(prep_res)
def _run(self,shared): p=self.prep(shared); e=self._exec(p); return self.post(shared,p,e)
def run(self,shared): 
    if self.successors: warnings.warn("Node won't run successors. Use Flow.") 
```



## 关于PocketFlow的语法糖

为了实现下面的用于构建Flow的语法糖

```python
node  >> next_node  # 设置一个结点的默认后继结点 即 default 的action时候的next node
node - "action" >> next_node # 设置一个结点在某action下的next node
```

我们需要在 `BaseNode` 类中提供下面的运算符重载，分别重载入 `__rshift__` 运算符（>>）和 `__sub__` 运算符 （-） 将 前者翻译为调用 `next` 方法来设置 next node 后者则在检查字符串合法性后，返回一个`_ConditionalTransition` 内部类方便下一步的使用。

```python
def __rshift__(self,other): return self.next(other)
def __sub__(self,action):
	if isinstance(action,str): return _ConditionalTransition(self,action)
	raise TypeError("Action must be a string")
```

这个辅助的内部类用于暂存 重载后的 `__sub__` 的结果，从而实现第二个更为复杂的语法糖。

```python
class _ConditionalTransition:
    def __init__(self,src,action): self.src,self.action=src,action
    def __rshift__(self,tgt): return self.src.next(tgt,self.action)
```

## Node

实现我们的可执行基本结点，他需要包含自动重试的功能避免 `exec` 中请求的 LLM 函数输出结果的不可靠性。同时由于其可能必然不可靠，我们也需要实现出错降级的功能而不要因为出错导致崩溃。

作为最核心的定义部分，我们需要给出新的类，继承父类的相关参数并且给出新的所需参数。使用继承类来获取前面全部的所有属性的和方法，增加了两个新的参数，使用 `super().__init__()` 来执行父类的构造函数来保证可靠的初始化，并且将Node的外部参数加载到的类参数中来方便使用。

```python
class Node(BaseNode):
    def __init__(self,max_retries=1,wait=0): super().__init__(); self.max_retries,self.wait=max_retries,wait

```

我们还需要定义备用方法来实现出错后的优雅回退，当然他现在是空的，只提供了抛出错误的功能。

```python
def exec_fallback(self,prep_res,exc): raise exc
```

作为可以可以真实被执行的类，我们需要结合重试与回退机制重写执行流程，这里就体现了执行逻辑和函数逻辑分离 `exec` 方法 和 `_exec` 方法的优势，我们去重写  `_exec`  即可。他需要实现自动重试并记录重试次数，出错次数过多后自动调用回退方法，不会死循环也不会产生代码退出的异常。

```python
    def _exec(self,prep_res):
        for self.cur_retry in range(self.max_retries):
            try: return self.exec(prep_res)
            except Exception as e:
                if self.cur_retry==self.max_retries-1: return self.exec_fallback(prep_res,e)
                if self.wait>0: time.sleep(self.wait)
```



## Flow

我们来介绍整个流程的控制器，从抽象设计的角度看，Flow是Node的集合，但从代码设计的角度看，Flow是一个入口，是执行一系列结点的开始。他本身继承自一个 `BaseNode` 因此Flow支持各种复杂的嵌套结构，允许多层嵌套，同时为了展现他的特殊性，我们为一个Flow设置特殊的属性 `start_node`  ，同时增加设置这个参数的函数。源代码如下

```python
class Flow(BaseNode):
    def __init__(self,start=None): super().__init__(); self.start_node=start
    def start(self,start): self.start_node=start; return start
```



为了让整个Flow可以正常的运行，我们需要让他指导究竟谁是下一个结点，因此给出一个新的方法，他自动的根据当前结点 `curr` 的 `action` 以及 `successors` 中去寻找谁是下一个结点，并在非终止结点跳出的时候给出警告，提醒我们什么样的动作让我们跳出了。如果没有后继结点，此方法返回 `None`	

```python
    def get_next_node(self,curr,action):
        nxt=curr.successors.get(action or "default")
        if not nxt and curr.successors: warnings.warn(f"Flow ends: '{action}' not found in {list(curr.successors)}")
        return nxt

```



为了编排整个Flow的执行逻辑，我们提供内部方法来完全的替代 `_exec` 方法，虽然 Flow 也继承自BaseNode 但是执行逻辑和单个结点并不相符，因此要提供单独的方法来进行Flow的执行编排。

```python
    def _orch(self,shared,params=None):
        curr,p,last_action =copy.copy(self.start_node),(params or {**self.params}),None
        while curr: curr.set_params(p); last_action=curr._run(shared); curr=copy.copy(self.get_next_node(curr,last_action))
        return last_action

```

- **`curr, p, last_action = ...`**: 初始化三个变量。
  - `curr`: 当前要执行的节点。`copy.copy(self.start_node)` 创建起始节点的**一个副本**。这很重要，可以防止多次运行流程时节点状态互相干扰。
  - `p`: 当前节点的参数。它是一个合并了传入的 `params` 和流程自身 `self.params` 的新字典，并以传入的参数作为第一优先级，外层Flow的参数覆盖内层`{**self.params}` 是一种复制字典的写法。
  - `last_action`: 记录上一个节点返回的动作，初始为 `None`。
- **`while curr:`**: `while` 循环，只要 `curr` 不是 `None`（即还有下一个节点），就一直循环下去。
- **`curr.set_params(p)`**: 为当前节点设置参数。
- **`last_action = curr._run(shared)`**: 运行当前节点，并把它返回的结果（也就是下一个动作）存起来。
- **`curr = copy.copy(self.get_next_node(curr, last_action))`**: 根据当前节点和它返回的动作，找到下一个节点，并创建它的副本，赋值给 `curr`，为下一次循环做准备。
- **`return last_action`**: 当循环结束（`curr` 变为 `None`），返回最后一个节点的执行结果。



整理整个Flow，我们修改了作为入口执行逻辑的`_run` 方法和 `post` 方法，将执行 `_exec` 改为执行 `_orch` ，并且设置了整个 Flow 的返回：最后一个结点执行后的返回值（一个字符串）。

```python
    def _run(self,shared): p=self.prep(shared); o=self._orch(shared); return self.post(shared,p,o)
    def post(self,shared,prep_res,exec_res): return exec_res

```



**我们在Flow中第一次见到了参数这个BaseNode基本属性被修改，他的作用是提供一个Shared字典之外的，可以被大家访问的，在运行的时候固化的用来描述一些执行情况需求的数据，如果我们需要使用`paras`，则需要在手写Node的时候考虑对参数的访问** 由于 `(params or {**self.params})` 实现的逻辑，对于一个Flow，他的外部输入参数拥有最高的优先级会覆盖掉Flow内部本身的参数。



Flow 类预留了可以被重写的`prep` 和 `post` ，这个预留的位置为我们后面实现Flow的嵌套和重写他们实现一些特殊需求预留了空间。

## BatchNode

对Node类的继承，以支持批量处理来逐个的处理大量重复数据，他自然的获得了我们在Node类中实现的重试与自然的回退的能力。由于前面的部分清晰的区分了人工实现的 `exec`； 用于内部结点执行逻辑重写的 `_exec` , 用于内部整体逻辑的 `_run` 以及启动执行的接口 `run` 我们在BatchNode批量处理的逻辑中只需要重写内部结点执行逻辑 `_exec` 而完全不需要修改涉及执行部分的 `(_)run` 

```python
class BatchNode(Node):
    def _exec(self,items): return [super(BatchNode,self)._exec(i) for i in (items or [])]
```



我们要求**BatchNode在人工的`post`步中生成一个可迭代对象**，**并且无需修改人工实现的 `exec`** ，值得关注的是我们需要的 **`post` 步处理 BatchNode 的列表返回结构**。 新实现的代码通过列表推导式和父类的 `_exec` 实现了批量的处理，从而解决数据密集型任务。



## BatchFlow

相比于BatchNode希望处理数据密集任务，要反复的对同样格式的数据执行同一个处理工作，BatchFlow则允许我们批量的执行一些结构完全一致，但是涉及不同内容的Flow。每次都使用不同的 `params` 。可以把它想象成一个循环，它会针对每个参数集重复运行该流，所有对`Shared`字典的修改都需要在Node中实现，原则上BatchFlow只是一个调度器，和Flow一样负责调度结点。



我们要求BatchFlow被重写 `prep` 步（在实例化之前的类重写，和BatchNode一样），并且`prep`方法返回一个参数列表（字典组成的列表），每个元素都是一组用于运行流程的参数。BatchFlow的作用是对于每一组参数，都运行一个整个流程 `_orch` ，在运行BatchFlow的时候，内部拥有的对应的参数是流程自身的参数和这组特定参数的合并。只需要修改 `_run` 方法就可以实现BatchFlow

```python
class BatchFlow(Flow):
    def _run(self,shared):
        pr=self.prep(shared) or []
        for bp in pr: self._orch(shared,{**self.params,**bp})
        return self.post(shared,pr,None)
```



可以将一个 **BatchFlow** 嵌套在另一个 **BatchFlow** 中，由于BatchFlow的特殊设计，他会将所有BatchFlow层中的参数进行合并再传给最内层的结点。在实际的执行中，是从外部的第一个参数开始遍历内层的全部参数，然后逐个执行最基础的Flow , BatchFlow的内部可以嵌套单个的结点或者多节点的组成的Flow，没有本质区别，**使用BatchNode的首要抽象设置是，我们需要Node以什么样的参数循环往复运行，而不是固定Node只变换 `shared` 的数据**

## Async

现在我们开始研究异步类，代码进入了异步世界。核心区别是使用 `async`/`await` 关键字。

- **`async def`**: 定义一个“协程”函数，也就是异步函数。**它可以在执行过程中暂停（`await`）**，让出控制权。
- **`await`**: **只能在 `async def` 函数内部使用。它表示“等待这个异步操作完成”**，在等待期间，程序可以去执行其他任务。

在异步编程中，`await`的真正含义是“**暂停我当前的任务，把CPU控制权交出去，让其他任务先跑。等这个耗时的I/O操作完成了，再通知我，我继续往下走。**” 从而避免整个程序因为一个IO的卡顿导致程度的卡顿。至于Async内部是如何实现异步的，Python如何管理他，这里不考虑



由于 Async 编程并不像基础程序那样被熟悉，这里单独介绍一个相关的知识。对于进行Async编程，我们需要注意下面的规则

1. **定义时用 `async def`**：任何函数/方法，如果其内部使用了 `await`，那么这个函数/方法在定义时**必须**在 `def` 前加上 `async`。
2. **调用时用 `await`**：调用一个 `async def` 定义的函数时，**必须**使用 `await` 关键字。
3. **传染性**：这是一个非常重要的特性。如果一个函数 `A` 内部 `await` 了另一个函数 `B`，那么函数 `A` 本身也必须被定义为 `async def`。这个规则会一直向上传递，直到最顶层的调用者，也就是下层的异步会不断因为调用而传染到上层所有的程序。

**注意，在我们使用异步的所有结点和Flow的时候，由于我们的各个方法都是异步的，因此重写`prep`  `exec`,`post`** 的时候所有的有IO的地方都应该增加 `await` ；在创建函数包含异步结点和异步流的时候，需要使用 `async` 关键字和对`flow.run_async` 方法使用 `await` 关键字。在从同步函数启动异步函数的时候，需要使用 

```python
# asyncio.run 是连接同步世界和异步世界的桥梁
asyncio.run(main())
```



## AsyncNode

我们现在重写整个异步的结点，他将从普通的节点中继承，并且重写所有和异步相关的方法。

```python
class AsyncNode(Node):
    async def prep_async(self,shared): pass
    async def exec_async(self,prep_res): pass
    async def exec_fallback_async(self,prep_res,exc): raise exc
    async def post_async(self,shared,prep_res,exec_res): pass
```

异步的预留了我们需要自己重写的业务逻辑相关的方法，所有的方法的名称都进行了对应的修改来避免混淆，在我们自己重写这些方法的时候需要注意在涉及等待的任务上进行 `await` 让AsyncNode以更加性能友好的方式读取数据，调用LLM并等待，等待用户反馈或协调多个Agent。



重写重试和回退的逻辑（逻辑本身不变），这里用户基本无需关心，这里大量的使用 `await` 关键字核心是因为需要使用异步函数，因此产生了传染。`asyncio.sleep` 是协程休眠的函数，不会阻塞整个程序。

```python
    async def _exec(self,prep_res): 
        for self.cur_retry in range(self.max_retries):
            try: return await self.exec_async(prep_res)
            except Exception as e:
                if self.cur_retry==self.max_retries-1: return await self.exec_fallback_async(prep_res,e)
                if self.wait>0: await asyncio.sleep(self.wait)

```



下面我们需要提供 `run` 的异步版本，逻辑本身是不变的但是因为传染因此引入了`await` 并且限制了我们一定要通过包含异步命名的`run_async` 方法来启动结点，如果使用以前的方法则直接抛出`RuntimeRrror` 

```python
    async def run_async(self,shared): 
        if self.successors: warnings.warn("Node won't run successors. Use AsyncFlow.")  
        return await self._run_async(shared)
    async def _run_async(self,shared): p=await self.prep_async(shared); e=await self._exec(p); return await self.post_async(shared,p,e)
    def _run(self,shared): raise RuntimeError("Use run_async.")

```



只运行一个 `AsyncNode`，并且没有添加其他并行任务，我们将不会获得Async带来的性能提升，而是不阻塞的效果，在运行到对应的 `AsyncNode` 的时候，程序在等待IO的时候不产生阻塞问题，从而为其他程序执行预留CPU。



## AsyncFlow

`AsyncFlow` 多重继承，既有 `Flow` 的编排能力，又有 `AsyncNode` 的异步特性。

```python
class AsyncFlow(Flow,AsyncNode):
    async def _orch_async(self,shared,params=None):
        curr,p,last_action =copy.copy(self.start_node),(params or {**self.params}),None
        while curr: curr.set_params(p); last_action=await curr._run_async(shared) if isinstance(curr,AsyncNode) else curr._run(shared); curr=copy.copy(self.get_next_node(curr,last_action))
        return last_action

```

和同步版本的完全一致，增加了一些 `await` 关键字来实现异步，并且支持我们在一个异步Flow中混合两类Node

- 异步版本的编排器。
- **`isinstance(curr, AsyncNode)`**: 检查当前节点是不是一个异步节点。
- **`await curr._run_async(shared) if ... else ...`**: 这是一个三元表达式。如果是异步节点，就用 `await` 调用它的 `_run_async`；如果不是（是同步节点），就直接调用它的 `_run`。这使得一个异步流程中可以混合使用同步和异步节点。



## AsyncBatch

全部采取了多重继承，包括Node和Flow。

对于AsyncBatchNode 有

```python
class AsyncBatchNode(AsyncNode,BatchNode):
    async def _exec(self,items): return [await super(AsyncBatchNode,self)._exec(i) for i in items]
```

- **多重继承**: 同时继承 `AsyncNode` 和 `BatchNode`。
- 它的 `_exec` 方法遍历列表，对每个项目 `await` 父类的 `_exec`。这是**顺序**执行的



对于AsyncBatchFlow有

```python
class AsyncBatchFlow(AsyncFlow,BatchFlow):
    async def _run_async(self,shared):
        pr=await self.prep_async(shared) or []
        for bp in pr: await self._orch_async(shared,{**self.params,**bp})
        return await self.post_async(shared,pr,None)

```

- 异步版本的批量流程，**顺序**执行多个流程实例。



## AsyncParallelBatch

AsyncParallelBatchNode 有

```python
class AsyncParallelBatchNode(AsyncNode,BatchNode):
    async def _exec(self,items): return await asyncio.gather(*(super(AsyncParallelBatchNode,self)._exec(i) for i in items))

```

- **`asyncio.gather(...)`**: 这是实现**并行**的关键。它接收一个协程列表，然后同时启动它们，并等待所有协程都完成。
- **`(... for i in items)`**: 这是一个生成器表达式，`*` 号把它展开成多个参数，相当于 `asyncio.gather(coro1, coro2, coro3, ...)`。



AsyncParallelBatchFlow有

```python
class AsyncParallelBatchFlow(AsyncFlow,BatchFlow):
    async def _run_async(self,shared): 
        pr=await self.prep_async(shared) or []
        await asyncio.gather(*(self._orch_async(shared,{**self.params,**bp}) for bp in pr))
        return await self.post_async(shared,pr,None)

```

- **并行**版本的批量流程。使用 `asyncio.gather` 同时启动多个流程实例。