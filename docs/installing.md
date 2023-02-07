## Installation

In your machine run:
```
git clone https://github.com/binpash/dynamic-parallelizer.git
cd ./dynamic-parallelizer.git
./scripts/install_deps_ubuntu20.sh

```

<!-- ### Setting up Dev Workspace

It is *strongly recommended* to clone the dynamic parallelizer into a 
VsCode Dev Container (ms-vscode-remote.remote-containers).
Assuming you have already installed the extension,
clone the repository inside a Dev Container using the shortcut `Ctrl` + `Shift` + `P` (`Cmd` + `Shift` + `P` for MacOS)
and select `Dev Containers: Clone Repository in Container Volume`.

### Installing Riker

Riker is used for tracing purposes. In order to set up riker
run the following commands,
in the container's terminal (`Ctrl` + `"+"` | `Ctrl` + `~` for MacOS):

```
git submodule update --init --recursive
cd ./deps/riker/
make
sudo make install
cd ../../
``` -->

### Setting up Cloudlab

As of now, the dynamic parallelizer tests are run on an Ubuntu Virtual Machine hosted on [Cloudlab](https://www.cloudlab.us/).
It is *strongly recommended* to also use Cloudlab's infrastracture.
To do so, you need to set up a Cloudlab account and join PaSh's workspace.

Set up a machine with the following specs:
* **Selected profile:** small-lan:34
* **Number of Nodes:** 1
* **Select OS Image:** Default Image
* **Optional physical node type:** c6525-25g
* **Name:** whatever you like
* **Project:** PaSh
* **Start date/time:** blank
* **Experiment duration:** 16 hours

Virtual machine creation typically takes less than 5 minutes.
When the VM has booted,
click on `node0` icon of `Topology View` and select `Shell` to open a new terminal.

<!-- #### Set up SSH keys
The first time you sign up in Cloudlab you will need to set up your [SSH keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent).
You can upload you SSH public key on Cloudlab [here](https://www.cloudlab.us/ssh-keys.php). You will only need to follow this step **once**.

After generating the keys, 
update `scripts/vars_template.sh` (**in your Dev Container**)
to point to the SSH private key file that corresponds to the key you just uploaded.

#### Get VM IP address
You can use `ifconfig` in your Cloudlab VM to get your machine's IP address.Copy the `inet` field (128. ...) and paste it on `scripts/vars_template.sh` (**in your Dev Container**)

#### Set target username

Replace the `cloudlab_user` field in `scripts/vars_template.sh`
(**in your Dev Container**) with your Cloudlab username.

#### Upload to Dev Container to Cloudlab

In order to push the Dev Container changes to Cloudlab, run:
```
./scripts/upload-to-cloudlab.sh
``` -->

### Running tests

As of now, tests are only able to run on the Cloudlab machine
(we will fix this later).

Run the following: 
```
cd test
./test_orch.sh
```
