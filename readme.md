## 四川大学微服务自动打卡工具

### 更新日期 2023/01/20

### 说明  <a id="introduction"></a>

------

本工具主要用于解决学校现在还保留着的形式主义打卡。针对改版后的打卡重新编写了打卡逻辑，同时重构了部分代码


### 本项目特色 <a id="special"></a>

--------

* 支持cookie/账号密码两种方式打卡
    * 默认使用cookie方式登录，这种方式登录不需要配置验证码识别
    * 在没有提供默认cookie，或是cookie登录失败的情况下自动降级到账号密码登录，此时需要调用验证码识别接口
* 使用本地验证码识别平台进行识别，不依赖外部提供的api，运行更加稳定
    * 验证码识别平台请参见 [kerlomz/captcha_platform](https://github.com/kerlomz/captcha_platform)
    * 项目中验证码识别网络模型准确率大约在96%左右，在服务器上每张验证码的识别用时大约在0.03s左右，应该比绝大部分打码平台的返回速度要快
* 使用SQLite数据库，不需要在服务器上配置其他数据库


### 与其他打卡工具的对比  <a id="difference"></a>

--------------

| 项目名                                                                        | 登陆实现方式                   | 数据来源    | 数据库类型  |
|----------------------------------------------------------------------------|--------------------------|---------|--------|
| [SCU-ncov-auto-check](https://github.com/randomCui/SCU-ncov-auto-check)    | 账号密码(本地识别验证码) / cookie登陆 | 上次填报数据  | SQLite |
| [SCU-ncov_checkpoint](https://github.com/somenothing/SCU-ncov_checkpoint)  | 账号密码(外部识别验证码)            | 上次填报数据  | MYSQL  |
| [scu-covid-auto-checkin](https://github.com/koinin/scu-covid-auto-checkin) | cookie登陆                 | 上次填报数据* | 无      |
| [ScuDaKa](https://github.com/shanzha09/ScuDaKa)                            | cookie登陆                 | 预置数据    | 无      |
| [scu-covid19](https://github.com/HyperMn/scu-covid19)                      | api登陆                    | 上次填报数据* | 无      |

> 全国可能有不少高校都使用了差不多的打卡模板，导致很多学校的打卡系统实际上可以通用，比如[scu-covid19](https://github.com/HyperMn/scu-covid19)就是从国科大的打卡脚本fork过来的<br>
> 但是**scu-covid19**项目***可能存在问题***，没有验证过其中使用的api是否适用于川带，并且填报的字段与川带目前填报的字段存在较大冲突，建议使用/开发时还是参考其他四个项目<br>

### 部署方式 <a id="deployment"></a>

----------------

1. 将本项目```git clone```到目录下
2. 激活```venv```虚拟环境
3. 执行```pip install -r requirements.txt```安装所需依赖
4. 部署[kerlomz/captcha_platform](https://github.com/kerlomz/captcha_platform)到本地，并启动其中的http服务
5. 运行```ncov_scheduler.py```

### 常见问题  <a id="common_question"></a>

------------
* 运行时报错，找不到Sqlite3库
> 在某些系统下，Python安装时可能不会安装Sqlite3库，如果不需要给多人打卡，一种替代方案是在ncov_post.py文件中增加要打卡的账号密码
> 
> 在文件末尾的代码中填入需要打卡的账号信息，之后使用定时工具定时运行即可

### 更新日志  <a id="update"></a>

----------
2023.1.20
- 重构了代码和数据库，支持cookie和账号密码登录两种方式，针对新的打卡重写了逻辑，目前可以实现正常打卡

8.1

- 数据库管理界面中增加了查看所有账户状态的选项

7.27

- 实现了一个非常基础的数据库管理功能，能够较为容易的增删改账号系统中的账号，做到了最起码的开箱即用功能
- 将倒计时精度由秒级上升到了微秒级

7.25

- 将程序中所有输出迁移到logging模块进行日志记录

7.24

- 修改了填报信息的发送格式，解决了填报信息与人工打卡不一致的Bug

7.22

- 增加了手动超控打卡开关的功能
 
7.21 

- 增加了每日打卡结果的数据库
