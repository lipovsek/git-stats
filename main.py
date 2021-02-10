from os import environ
from typing import List, Iterator, Iterable, Union, Dict
from itertools import chain

from github import Github
import pandas as pd
import matplotlib.pyplot as plt


class DataSource:
    def __init__(self) -> None:
        self.__github = Github(environ['TOKEN'])

    def __stars_raw(self, repos: List[str]) -> List[dict]:
        for repo in repos:
            data = [{"starred_at": sg.starred_at, "user": sg.user} for sg in self.__github.get_repo(repo).get_stargazers_with_dates()]
            yield (repo, data)

    def stars(self, repos: List[str]) -> Iterator[Iterable[Union[str, pd.DataFrame]]]:
        for repo_name, repo_data in  self.__stars_raw(repos):
            df = pd.DataFrame(repo_data).groupby(pd.Grouper(key="starred_at", freq='M')).count().rename(columns={"user": "stars_count"})
            df["stars_comulative"] = df["stars_count"].cumsum()
            yield (repo_name, df)

    def commits(self, repos: List[str]) -> Iterator[Iterable[Union[str, pd.DataFrame]]]:
            github_repo = self.__github.get_repo(repo)
            data = []
            for index, commit in enumerate(github_repo.get_commits()):
                if int(commit.last_modified.split(" ")[3]) < 2020:
                    break
                data.append({"last_modified": commit.last_modified, "repo": repo, "change": commit.stats.total})
            yield data


def stars(repos_all: Dict[str, List[str]]) -> None:
    ds = DataSource()
    stats = ("stars_count", "stars_comulative")
    for domain, repos in repos_all.items():
        starred_plot_data = dict(ds.stars(repos))
        fig, axes = plt.subplots(1, len(stats))
        for stat_ax, stat in enumerate(stats):
            for repo_name, repo_data in starred_plot_data.items():
                repo_data[stat].plot(label=repo_name, ax=axes[stat_ax])
            axes[stat_ax].set_title(stat)
            axes[stat_ax].legend()
        plt.show()
        fig.savefig(f"{domain}_stars.png")


if __name__ == "__main__": 
    repos = {"MLOps": ["bentoml/BentoML", "cortexproject/cortex", "kubeflow/kfserving"], "data_versioning": ["iterative/dvc", "mlflow/mlflow"]}
    commits(repos)
