# GitHub Actions 权限问题解决方案

## ❌ 错误信息

```
Error: Error 403: Resource not accessible by integration
```

## 🔍 问题原因

这个错误是因为 GitHub Actions 工作流没有足够的权限来创建 Release。GitHub 默认限制了 GITHUB_TOKEN 的权限。

## ✅ 解决方案

### 方案一：在工作流中添加权限配置（已修复）

我已经在所有工作流文件中添加了 `permissions` 配置：

```yaml
permissions:
  contents: write    # 允许创建 Release
  actions: read      # 允许读取 Actions 状态
  packages: write    # 允许写入包（如果需要）
```

**已更新的文件：**
- `.github/workflows/build-master.yml`
- `.github/workflows/build-slave.yml`
- `.github/workflows/build-manager.yml`
- `.github/workflows/release-all.yml`

### 方案二：在仓库设置中配置权限

如果方案一不起作用，可以手动配置仓库级别的权限：

1. 进入 GitHub 仓库
2. 点击 **Settings** (设置)
3. 在左侧菜单选择 **Actions** → **General**
4. 找到 **Workflow permissions** 部分
5. 选择 **Read and write permissions**
6. 勾选 **Allow GitHub Actions to create and approve pull requests**
7. 点击 **Save**

![Workflow Permissions Setting](https://docs.github.com/assets/cb-77934/mw-1440/images/help/settings/actions-workflow-permissions-write.webp)

### 方案三：使用 Personal Access Token

如果上述方法都不行，可以使用个人访问令牌：

1. **创建 Token：**
   - 访问 https://github.com/settings/tokens
   - 点击 **Generate new token (classic)**
   - 勾选权限：
     - ✅ `repo` (完整仓库访问)
     - ✅ `workflow` (工作流访问)
   - 生成并复制 Token

2. **添加为 Secret：**
   - 进入仓库 Settings → Secrets and variables → Actions
   - 点击 **New repository secret**
   - Name: `GH_TOKEN`
   - Value: 粘贴刚才生成的 Token
   - 点击 **Add secret**

3. **修改工作流：**
   在所有使用 `ncipollo/release-action` 的地方，将：
   ```yaml
   token: ${{ secrets.GITHUB_TOKEN }}
   ```
   改为：
   ```yaml
   token: ${{ secrets.GH_TOKEN }}
   ```

## 🧪 测试修复

推送一个新的标签来测试：

```bash
git tag v1.0.1-test
git push origin v1.0.1-test
```

然后查看 Actions 页面确认是否成功创建 Release。

## 📋 验证清单

- [ ] 工作流文件中包含 `permissions` 配置
- [ ] 仓库设置中 Workflow permissions 设置为 "Read and write"
- [ ] 如果是私有仓库，确认 Token 有足够权限
- [ ] 标签格式正确（以 v 开头，如 v1.0.0）

## 🔗 相关资源

- [GitHub Actions 权限文档](https://docs.github.com/en/actions/security-guides/automatic-token-authentication)
- [ncipollo/release-action 文档](https://github.com/ncipollo/release-action)
- [GITHUB_TOKEN 权限](https://docs.github.com/en/rest/overview/permissions-available-for-github_token)

## 💡 最佳实践

1. **最小权限原则** - 只授予必要的权限
2. **使用短期 Token** - 避免长期使用个人 Token
3. **定期轮换 Secret** - 定期更新 Token
4. **审计日志** - 定期检查 Actions 运行记录

---

**问题应该已经解决！** 现在重新触发工作流即可。🎉
