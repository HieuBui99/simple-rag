terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=3.0.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "test-rg" {
  name     = "test-resource" # Resource Group Name. The one above is an alias
  location = "Japan East"
  tags = {
    environment = "dev"
  }
}

resource "azurerm_virtual_network" "test-vnet" {
  name                = "test-network"
  resource_group_name = azurerm_resource_group.test-rg.name
  location            = azurerm_resource_group.test-rg.location
  address_space       = ["10.123.0.0/16"]

  tags = {
    environment = "dev"
  }
}

resource "azurerm_subnet" "test-subnet" {
  name                 = "test-subnet"
  resource_group_name  = azurerm_resource_group.test-rg.name
  virtual_network_name = azurerm_virtual_network.test-vnet.name
  address_prefixes     = ["10.123.1.0/24"]
}


resource "azurerm_public_ip" "test-ip" {
  name                = "test-ip"
  location            = azurerm_resource_group.test-rg.location
  resource_group_name = azurerm_resource_group.test-rg.name
  allocation_method   = "Dynamic"

  tags = {
    environment = "dev"
  }

}

resource "azurerm_network_interface" "test-nic" {
  name                = "test-nic"
  location            = azurerm_resource_group.test-rg.location
  resource_group_name = azurerm_resource_group.test-rg.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.test-subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.test-ip.id
  }

  tags = {
    environment = "dev"
  }
}


resource "azurerm_linux_virtual_machine" "test-vm" {
  name                = "test-vm"
  resource_group_name = azurerm_resource_group.test-rg.name
  location            = azurerm_resource_group.test-rg.location
  size                = "Standard_B2as_v2"
  admin_username      = "adminuser"
  network_interface_ids = [
    azurerm_network_interface.test-nic.id,
  ]

  custom_data = filebase64("docker.tpl")

  admin_ssh_key {
    username   = "adminuser"
    public_key = file("~/.ssh/azure_key.pub")
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts"
    version   = "latest"
  }

  tags = {
    environment = "dev"
  }
}

data "azurerm_public_ip" "instance-ip" {
  name                = azurerm_public_ip.test-ip.name
  resource_group_name = azurerm_resource_group.test-rg.name
}

output "public_ip_address" {
  value = "${azurerm_linux_virtual_machine.test-vm.name}: ${data.azurerm_public_ip.instance-ip.ip_address}"
}

# resource "azurerm_network_security_group" "test-sg" {
#     name                = "test-security-group"
#     location            = azurerm_resource_group.test-rg.location
#     resource_group_name = azurerm_resource_group.test-rg.name

#     security_rule {
#         name                       = "test-rule"
#         priority                   = 100
#         direction                  = "Inbound"
#         access                     = "Allow"
#         protocol                   = "*"
#         source_port_range         = "*"
#         destination_port_range    = "*"
#         source_address_prefix     = "*"
#         destination_address_prefix = "*"
#     }

#     security_rule {
#         name                       = "test-rule"
#         priority                   = 100
#         direction                  = "Outbound"
#         access                     = "Allow"
#         protocol                   = "*"
#         source_port_range         = "*"
#         destination_port_range    = "*"
#         source_address_prefix     = "*"
#         destination_address_prefix = "*"
#     }

#     tags = {
#         environment = "dev"
#     }
# }
