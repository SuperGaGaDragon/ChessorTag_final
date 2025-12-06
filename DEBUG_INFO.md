# Debug信息收集

## 请在浏览器控制台运行以下命令并提供输出：

### 1. 检查IS_HOST状态
```javascript
console.log('IS_HOST:', window.IS_HOST, 'PLAYER_SIDE:', window.PLAYER_SIDE);
```

### 2. 检查Elixir状态
```javascript
console.log('Elixir:', {
  side: elixirManager.side,
  currentElixir: elixirManager.currentElixir,
  pools: elixirManager.pools,
  maxElixir: elixirManager.maxElixir
});
```

### 3. 尝试部署时的详细日志
在B端尝试部署一个fighter（费用3），然后查看控制台输出，特别是：
- `[CLIENT] Checking elixir:` 这行的输出
- `[CLIENT] ElixirManager state:` 这行的输出

### 4. 检查elixir生成是否在运行
```javascript
console.log('elixirInterval:', elixirManager.elixirInterval !== null);
```

---

## 预期的问题

如果B端无法部署，可能的原因：
1. **elixir未正确同步**：CLIENT端的elixir值为0或不正确
2. **IS_HOST标志错误**：CLIENT端误认为自己是HOST
3. **缓存问题**：需要强制刷新（Cmd+Shift+R）

---

## 临时解决方案

如果急需测试，可以在控制台临时修改elixir值：
```javascript
elixirManager.setElixir('b', 10);
```
