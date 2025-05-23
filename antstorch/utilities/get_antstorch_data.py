import torchvision
import os

def get_antstorch_data(file_id=None,
                       target_file_name=None,
                       antstorch_cache_directory=None):

    """
    Download data such as prefabricated templates and spatial priors.

    Arguments
    ---------

    file_id string
        One of the permitted file ids or pass "show" to list all
        valid possibilities. Note that most require internet access
        to download.

    target_file_name string
       Optional target filename.

    antstorch_cache_directory string
       Optional target output.  If not specified these data will be downloaded
       to the subdirectory ~/.antstorch/.

    Returns
    -------
    A filename string

    Example
    -------
    >>> template_file = get_antstorch_data('kirby')
    """

    def switch_data(argument):
        switcher = {
            "kirby": "https://ndownloader.figshare.com/files/25620107"
        }
        return(switcher.get(argument, "Invalid argument."))

    if file_id == None:
        raise ValueError("Missing file id.")

    valid_list = ("kirby",
                  "show")

    if not file_id in valid_list:
        raise ValueError("No data with the id you passed - try \"show\" to get list of valid ids.")

    if file_id == "show":
       return(valid_list)

    url = switch_data(file_id)

    if target_file_name is None:
        target_file_name = file_id + ".nii.gz"

    if antstorch_cache_directory is None:
        antstorch_cache_directory = os.path.join(os.path.expanduser('~'), '.antstorch/')
    target_file_name_path = os.path.join(antstorch_cache_directory, target_file_name)

    if not os.path.exists(target_file_name_path):
        torchvision.datasets.utils.download_url(url,
                                                antstorch_cache_directory,
                                                target_file_name)

    return(target_file_name_path)
