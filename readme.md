## 四川大学微服务自动打卡工具

### 说明  <a id="introduction"></a>

------

本项目的初衷是解决目前现存微服务打卡的两大问题

1. 需要调用selenium webdriver 因此需要桌面端环境* 不能在无桌面环境的服务器上运行
2. 识别验证码需要依赖外部接口 可能引入付费问题

> * 实际上在纯命令行环境也可以使用chrome-headless等无GUI的浏览器达到纯命令行操作效果，因此第一点其实也不是什么问题


### 本项目特色 <a id="special"></a>

--------

* 未使用selenium模块进行构建，不需要调用浏览器完成数据填报，对于命令行环境更加友好
    * 自带较为完善的日志记录功能
    * 不使用cookie或是api直接进行填报，直接模拟人工手动登陆的方式，更加接近真人操作
* 使用本地验证码识别平台进行识别，不依赖外部提供的api，运行更加稳定
    * 验证码识别平台请参见 [kerlomz/captcha_platform](https://github.com/kerlomz/captcha_platform)
    * 项目中验证码识别网络模型准确率大约在96%左右，在服务器上每张验证码的识别用时大约在0.03s左右，应该比绝大部分打码平台的返回速度要快<br>【谁让我服务器搭在本地了XD
* 使用SQLite数据库，免去配置MYSQL的麻烦，尽力做到开箱即用
    * 提供一个简易数据库操作程序，可以通过简单的命令行进行打卡账号的增加、删除、修改


### 与其他打卡工具的对比  <a id="difference"></a>

--------------

| 项目名                                                                        | 登陆实现方式   | 填报实现方式  | 数据来源    | 地址数据来源 | 数据库类型  | 是否支持虚拟定位 |
|----------------------------------------------------------------------------|----------|---------|---------|--------|--------|----------|
| [SCU-ncov-auto-check](https://github.com/randomCui/SCU-ncov-auto-check)    | 本地识别验证码  | 网页url填报 | 上次填报数据  | 上次     | SQLite | 不支持      |
| [SCU-ncov_checkpoint](https://github.com/somenothing/SCU-ncov_checkpoint)  | 外部识别验证码  | 网页url填报 | 上次填报数据  | 上次     | MYSQL  | 支持       |
| [scu-covid-auto-checkin](https://github.com/koinin/scu-covid-auto-checkin) | cookie登陆 | 网页url填报 | 上次填报数据* | 预置地址   | 无      | 不支持      | 
| [ScuDaKa](https://github.com/shanzha09/ScuDaKa)                            | cookie登陆 | 网页url填报 | 预置数据    | 预置地址   | 无      | 不支持      |
| [scu-covid19](https://github.com/HyperMn/scu-covid19)                      | api登陆    | api填报   | 上次填报数据* | 上次*    | 无      | 不支持      |

> 全国可能有不少高校都使用了差不多的打卡模板，导致很多学校的打卡系统实际上可以通用，比如[scu-covid19](https://github.com/HyperMn/scu-covid19)就是从国科大的打卡脚本fork过来的<br>
> 但是**scu-covid19**项目***可能存在问题***，没有验证过其中使用的api是否适用于川带，并且填报的字段与川带目前填报的字段存在较大冲突，建议使用/开发时还是参考其他四个项目<br>

### 需求 <a id="requirement"></a>

---------------


```requests``` 用于网页数据请求

```beautifulsuop4```用于解析网页数据

```prompt-toolkit2```用于数据库管理界面的构建，如果不需要使用可以不安装

其余库均为python内建库

### 部署方式 <a id="deployment"></a>

----------------

1. 将本项目```git clone```到目录下
2. 激活```venv```虚拟环境
3. 执行```pip install -r requirements.txt```安装所需依赖
4. 部署[kerlomz/captcha_platform](https://github.com/kerlomz/captcha_platform)到本地，并启动其中的http服务
5. 运行```ncov_launcher.py```文件（初次运行可能会报错)
   1. 如果出现报错，多半是因为数据库中没有打卡账号数据，需要自己手动将信息填入数据库中。之后重新运行文件
   2. ```ncov_launcher```文件自带每日定时打卡功能，无需设置定时任务

### 常见问题  <a id="common_question"></a>

------------

* 为什么这个脚本和[SCU-ncov_checkpoint](https://github.com/somenothing/SCU-ncov_checkpoint)看起来基本上差不多
  * 本来开发对标的就是这个项目，最初是因为我以为selenium不能在命令行界面使用，并且希望不使用外部api识别验证码，不配置MYSQL才开始开发的。直到我在开始写readme的时候才发现chrome也能在无桌面环境的情况下使用，这下算是绕了个大弯了。
* 怎么将服务部署到服务器上呢
  * 之后会更新部署方法，可能还会开发一个代理打卡的功能，什么时候被学校查水表了我就跑路(x) 
* 运行时报错，找不到Sqlite3库
> 在某些系统下，Python安装时可能因为缺乏依赖导致没有Sqlite3库，如果不需要给多人打卡，一种替代方案是在ncov_post.py文件中增加要打卡的账号密码，在文件末尾的代码中
> ````
> if __name__ == '__main__':
>
> ncov_post('', '')  <-----填入这里
> ````
> 填入需要打卡的账号信息，之后使用定时工具定时运行即可

### 开发计划  <a id="plan"></a>

----------------

- 增加虚拟定位的功能
- 完成cookie登陆的选项
- 增加随机延时打卡功能，避免在十二点扎堆打卡造成问题
- ~~引入/编写一个简单管理数据库的程序，更加便于上手~~ 【已完成

### 更新日志  <a id="update"></a>

----------

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
