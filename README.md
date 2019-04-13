# rocketsimu
ハイブリッドロケット用6自由度弾道シミュレーションライブラリ  
v0.1.0:minimum library

# Features
- パッケージ化(依存ライブラリは自動インストールされます)
- 6自由度弾道シミュレーション
- べき法則風モデル

# Dependencies
- numpy
- numpy-quaternion
- scipy
- pandas

# Installation
## Clone
以下のコマンドからgitを使用して作業ディレクトリにクローンするか，
[https://github.com/PLANET-Q/rocketsimu](https://github.com/PLANET-Q/rocketsimu)の 'Clone or Download' ボタンよりZIPファイルをダウンロードして展開します。
```
cd [ダウンロード先フォルダ]
git clone https://github.com/PLANET-Q/rocketsimu
cd rocketsimu
```

## Install
カレントディレクトリを作業ディレクトリに移してから，以下のコマンドでrocketsimuをインストールします。
```
python setup.py install
```
`numpy`， `scipy`などの依存パッケージは自動でインストールされますが， `numpy-quaternion`のみ手動でインストールする必要があります。  
以下のコマンドより`numpy-quaternion`モジュールをインストールしてください。
```
pip install numpy-quaternion
```

## Uninstall
アンインストールしたい場合は以下のコマンドで削除できます。
```
pip uninstall rocketsimu
```

# Usage
[サンプルコード](https://github.com/PLANET-Q/rocketsimu/samples/sample.py)を参照。
パラメータの設定については[howto_setting_params](https://github.com/PLANET-Q/rocketsimu/docs/howto_setting_params.md)を参照してください。

# Future works/TODO
- インターフェース実装
- **コードリファクタリング**
- 95パーセンタイル統計風モデル
- 予報風対統計風誤差統計モデル
- 落下分散導出
- 地図上への弾道/落下分散プロット
- GUI実装(ライブラリ→ツールキットへ)
- 逆問題設計

# Thanks/Acknowledgements
- [shugok](https://github.com/shugok): シミュレーションの本質部分であるソルバ関数へ渡すdu_dt導出関数のアルゴリズムのほぼ全てを提供していただきました。

# LICENSE
このプロジェクトは[MITライセンス](https://github.com/PLANET-Q/rocketsimu/blob/master/LICENSE)のもと公開されています。以下の制限のもと利用可能です。
- このプロジェクト内のソースコードは誰でも自由に利用/改変/再頒布可能ですが，このスクリプトを利用するソースコード内の重要な箇所に著作権表示と[本ライセンス表示](https://github.com/PLANET-Q/TrajecSimu2/blob/master/LICENSE)を付ける必要があります。  
- **このプロジェクト内のソースコードについて作者/著作権者は一切の責任を負いません**