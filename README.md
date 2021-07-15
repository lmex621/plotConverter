# plotConverter
chia公式poolが実装される前から作成可能だったOG plot(solo farm用)をchia公式のpoolファーミング対応のportable plotに変換するソフトウェアです。
This software converts an OG plot (for solo farm), which was available before the implementation of the official chia pool, into a portable plot for the official chia pool farming.

# 使用に伴う事 before using this program
このソフトウェアの使用に伴い、chia公式のクライアントにてplotファイルを認識する事は確認出来ています。ただ、pool側においてspaceが増加することと実際に当選する事、そして変換したplotにおいて正常な配当が発生するかに関しては確認していません。また、この変換ソフトを用いることによって生じるいかなる問題に関してもこのプログラム製作者は責任を負いません。自己責任の元で使用してください。
また、一応何か問題がある可能性があるため、変換したplotファイルはいずれ再生成を行うことをお勧めします。

With the use of this software, we have confirmed that the official CHIA client recognizes the plot file. However, we have not confirmed that the pool will increase the space, that it will actually win, or that the converted plot will generate normal payouts. In addition, the producer of this program is not responsible for any problems caused by using this conversion software. Please use it at your own risk.
It is recommended that you regenerate the converted plot file at some point to avoid any possible problems.

# 利用方法 how to use
__使用前に102GiB以上の空き容量を確保してください。一時的にplotファイルが複製されます。__
__Please make sure you have at least 102 GiB of free space before use. Plot files will be temporarily duplicated.__

python3.8以降のインストールを公式サイトから行います。pythonへのpathも通してください。
Install python 3.8 or later from the official website, including the path to python.

その後、以下のサイトからVisual c++ランタイムをダウンロード、インストールをします。
After that, download and install the Visual c++ Runtime from the following site.
https://support.microsoft.com/en-us/topic/the-latest-supported-visual-c-downloads-2647da03-1eea-4433-9aff-95f26a218cc0

そしたら、cmdにて以下のコードを走らせます。
Then, run the following code in cmd.

for Windows
```
python -m pip install --upgrade pip
python -m pip install blspy
```

for Linux,Ubuntu
```
pip install --upgrade pip
pip install blspy
```

次に当githubに公開されているconvert.pyをcloneします。またはgithubのサイトからソースコードのダウンロードを行います。
Next, clone convert.py, which is available on our github. Alternatively, you can download the source code from the github site.
```
git clone https://github.com/MicotoTisaki/plotConverter.git
```

次にconvert.pyを何かしらのeditorで開き、11,12行目の変数を編集します。
Next, open convert.py in some kind of editor and edit the variables in lines 11 and 12.
```
new_puzzle_key = 'aaa'
new_farmer_key = 'bbb'
```
ここにはplotファイルを生成する際のPool Contract Addressをaaaの所に、Farmer Public Keyをbbbの所に代入します。上書き保存したらconvert.pyをplotファイルがあるディレクトリにコピーします。
Assign the Pool Contract Address to aaa and the Farmer Public Key to bbb when generating the plot file. After overwriting and saving, copy convert.py to the directory where the plot file is located.

D:¥
 |- aaaa.plot
 |- bbbb.plot
 |- cccc.plot
 |- convert.py

このように配置できたら、cmdからconvert.pyを走らせます。
Once this is in place, run convert.py from cmd.

```
>D:
>python convert.py
```

変換が終了すると、OG plotは全て削除され、/create/aaaa.plotとcreateフォルダの下に変換後のファイルが生成されます。
When the conversion is finished, all OG plots will be deleted and the converted files will be generated under the /create/aaaa.plot and create folders.

また、変換候補のファイルにportable plotが入っている場合はスキップされOG plotのみを候補に変換を行います。
Also, if the candidate file contains a portable plot, it will be skipped and only the OG plot will be converted.

# 投げ銭 how to support
XCH:xch124zmvg9g59sauqhmvdryd58skhgsmrud5npn76xe3tgt6ujegdsspk9msh
